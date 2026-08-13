"""Real Dovecot process and external IMAP controls for Mail acceptance."""

from __future__ import annotations

import contextlib
import datetime
import getpass
import grp
import imaplib
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time


_APPEND_UID = re.compile(rb"\[APPENDUID\s+\d+\s+(\d+)\]")


class DovecotHarness:
  """Own one disposable loopback Dovecot instance and its external client."""

  username = "acceptance@inkcre.local"
  password = "acceptance-pass"  # noqa: S105 - disposable loopback fixture

  def __init__(self, distribution_root: Path, work_root: Path):
    self.distribution_root = distribution_root
    self.runtime = Path(tempfile.mkdtemp(prefix="inkcre-mail-acceptance.", dir=work_root))
    self.port = self._reserve_port()
    self.process: subprocess.Popen[bytes] | None = None
    self._output = None

  @staticmethod
  def _reserve_port() -> int:
    with socket.socket() as probe:
      probe.bind(("127.0.0.1", 0))
      return int(probe.getsockname()[1])

  @property
  def binary(self) -> Path:
    return self.distribution_root / "install" / "sbin" / "dovecot"

  def start(self) -> None:
    if not self.binary.is_file():
      raise RuntimeError(f"Dovecot binary is unavailable: {self.binary}")
    for child in ("etc", "run", "state", "log", "mail/home"):
      (self.runtime / child).mkdir(parents=True, exist_ok=True)
    config = self.runtime / "etc" / "dovecot.conf"
    config.write_text(self._configuration(), encoding="utf-8")
    output_path = self.runtime / "log" / "process.log"
    self._output = output_path.open("ab")
    environment = os.environ.copy()
    extra_libraries = os.getenv("INKCRE_DOVECOT_DYLD_LIBRARY_PATH")
    if extra_libraries:
      current = environment.get("DYLD_LIBRARY_PATH")
      environment["DYLD_LIBRARY_PATH"] = (
        extra_libraries if not current else f"{extra_libraries}:{current}"
      )
    self.process = subprocess.Popen(  # noqa: S603 - validated acceptance binary
      [str(self.binary), "-F", "-c", str(config)],
      cwd=self.runtime,
      env=environment,
      stdout=self._output,
      stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + 10
    last_error: Exception | None = None
    while time.monotonic() < deadline:
      if self.process.poll() is not None:
        break
      try:
        with self.connect():
          return
      except (ConnectionError, OSError, imaplib.IMAP4.error) as error:
        last_error = error
        time.sleep(0.05)
    self.stop(preserve=True)
    detail = output_path.read_text(encoding="utf-8", errors="replace")
    raise RuntimeError(f"Dovecot did not become ready: {last_error}\n{detail}")

  def stop(self, *, preserve: bool = False) -> None:
    if self.process is not None and self.process.poll() is None:
      self.process.terminate()
      try:
        self.process.wait(timeout=5)
      except subprocess.TimeoutExpired:
        self.process.kill()
        self.process.wait(timeout=5)
    self.process = None
    if self._output is not None:
      self._output.close()
      self._output = None
    if not preserve:
      shutil.rmtree(self.runtime)

  @contextlib.contextmanager
  def connect(self):
    client = imaplib.IMAP4("127.0.0.1", self.port)
    try:
      client.login(self.username, self.password)
      yield client
    finally:
      with contextlib.suppress(imaplib.IMAP4.error, imaplib.IMAP4.abort, OSError):
        client.logout()

  def capabilities(self) -> set[str]:
    with self.connect() as client:
      status, values = client.capability()
      if status != "OK":
        raise RuntimeError(f"CAPABILITY failed: {values!r}")
      return {
        capability
        for value in values
        for capability in value.decode("ascii").upper().split()
      }

  def create_mailbox(self, name: str) -> None:
    with self.connect() as client:
      status, detail = client.create(name)
      if status not in {"OK", "NO"}:
        raise RuntimeError(f"CREATE {name!r} failed: {detail!r}")

  def append(
    self,
    mailbox: str,
    message: Path,
    *,
    internal_date: datetime.datetime,
    flags: tuple[str, ...] = (),
  ) -> int:
    rendered_flags = None if not flags else f"({' '.join(flags)})"
    with self.connect() as client:
      status, detail = client.append(
        mailbox,
        rendered_flags,
        internal_date,
        message.read_bytes(),
      )
    if status != "OK":
      raise RuntimeError(f"APPEND {mailbox!r} failed: {detail!r}")
    match = _APPEND_UID.search(b" ".join(detail))
    if match is None:
      raise RuntimeError(f"APPEND did not return one exact UID: {detail!r}")
    return int(match.group(1))

  def flags(self, mailbox: str, uid: int) -> set[str]:
    with self.connect() as client:
      client.select(mailbox)
      status, detail = client.uid("fetch", str(uid), "(FLAGS)")
    if status != "OK":
      raise RuntimeError(f"UID FETCH FLAGS failed: {detail!r}")
    rendered = b" ".join(item for item in detail if isinstance(item, bytes))
    match = re.search(rb"FLAGS \(([^)]*)\)", rendered)
    return set() if match is None else set(match.group(1).decode("ascii").split())

  def replace_flags(self, mailbox: str, uid: int, flags: tuple[str, ...]) -> None:
    with self.connect() as client:
      client.select(mailbox)
      status, detail = client.uid(
        "store",
        str(uid),
        "FLAGS.SILENT",
        f"({' '.join(flags)})",
      )
    if status != "OK":
      raise RuntimeError(f"UID STORE FLAGS failed: {detail!r}")

  def expunge(self, mailbox: str, uid: int) -> None:
    with self.connect() as client:
      client.select(mailbox)
      status, detail = client.uid("store", str(uid), "+FLAGS.SILENT", "(\\Deleted)")
      if status != "OK":
        raise RuntimeError(f"UID STORE \\Deleted failed: {detail!r}")
      status, detail = client.expunge()
      if status != "OK":
        raise RuntimeError(f"EXPUNGE failed: {detail!r}")

  def _configuration(self) -> str:
    user = getpass.getuser()
    group = grp.getgrgid(os.getgid()).gr_name
    return f"""dovecot_config_version = 2.4.4
dovecot_storage_version = 2.4.4

base_dir = {self.runtime / "run"}
state_dir = {self.runtime / "state"}
listen = 127.0.0.1
default_client_limit = 32
default_process_limit = 8
default_vsz_limit = unlimited
protocols {{
  imap = yes
}}

auth_allow_cleartext = yes
auth_mechanisms = plain login
ssl = no

mail_home = {self.runtime / "mail/home"}
mail_driver = maildir
mail_path = ~/Maildir
mail_uid = {os.getuid()}
mail_gid = {os.getgid()}
first_valid_uid = 1
default_internal_user = {user}
default_login_user = {user}
default_internal_group = {group}

namespace inbox {{
  inbox = yes
  separator = /
}}

passdb static {{
  password = {self.password}
}}

userdb static {{
  allow_all_users = yes
}}

service imap-login {{
  chroot =
  inet_listener imap {{
    port = {self.port}
  }}
}}

service imap-hibernate {{
  executable = imap
}}

log_path = {self.runtime / "log/dovecot.log"}
info_log_path = {self.runtime / "log/dovecot-info.log"}
"""
