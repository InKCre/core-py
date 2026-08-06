"""Producer grammar, normalization, and corrected relation direction."""

import datetime

import pydantic
import pytest

from app.business.info_base.main import InfoBaseManager
from app.schemas.info_base.block import BlockForm
from app.schemas.info_base.main import (
  GraphBlockForm,
  GraphForm,
  GraphRelationForm,
  InArcForm,
  OutArcForm,
  StarsGraphForm,
)
from app.schemas.info_base.relation import RelationForm
from extensions.mail.resolver import EmailResolver
from extensions.mail.schema import Email, EmailAddress


def test_base_creation_forms_exclude_database_managed_fields():
  assert set(BlockForm.model_fields) == {"storage", "resolver", "content"}
  assert set(RelationForm.model_fields) == {"content"}

  with pytest.raises(pydantic.ValidationError, match="extra_forbidden"):
    BlockForm.model_validate(
      {
        "id": 7,
        "resolver": "core.text.v1",
        "content": "not producer-owned",
      }
    )
  with pytest.raises(pydantic.ValidationError, match="extra_forbidden"):
    RelationForm.model_validate({"from_": 1, "to_": 2, "content": "not base-form-owned"})


@pytest.mark.parametrize(
  "graph",
  (
    {
      "blocks": [
        {"id": -1, "resolver": "core.text.v1", "content": "first"},
        {"id": -1, "resolver": "core.text.v1", "content": "duplicate"},
      ]
    },
    {
      "relations": [
        {"from_": -1, "to_": 8, "content": "unresolved"},
      ]
    },
    {
      "relations": [
        {"from_": 0, "to_": 8, "content": "zero"},
      ]
    },
  ),
)
def test_graph_form_rejects_invalid_command_local_id_structure(graph):
  with pytest.raises(pydantic.ValidationError):
    GraphForm.model_validate(graph)


def test_graph_form_accepts_new_and_existing_block_references():
  graph = GraphForm(
    blocks=(GraphBlockForm(id=-1, resolver="core.text.v1", content="new"),),
    relations=(GraphRelationForm(from_=42, to_=-1, content="interpretation"),),
  )

  assert graph.relations[0].from_ == 42
  assert graph.relations[0].to_ == -1


def test_stars_normalization_preserves_root_and_arc_direction():
  stars = StarsGraphForm(
    block=BlockForm(resolver="core.text.v1", content="root"),
    out_arcs=(
      OutArcForm(
        relation=RelationForm(content="outgoing"),
        to_graph=StarsGraphForm(
          block=BlockForm(resolver="core.text.v1", content="out child")
        ),
      ),
    ),
    in_arcs=(
      InArcForm(
        relation=RelationForm(content="incoming"),
        from_graph=StarsGraphForm(
          block=BlockForm(resolver="core.text.v1", content="in child")
        ),
      ),
    ),
  )

  graph = InfoBaseManager.normalize_graph(stars, id_start=-7)

  assert [(block.id, block.content) for block in graph.blocks] == [
    (-7, "root"),
    (-8, "out child"),
    (-9, "in child"),
  ]
  assert [
    (relation.from_, relation.content, relation.to_) for relation in graph.relations
  ] == [
    (-7, "outgoing", -8),
    (-9, "incoming", -7),
  ]


def test_mail_sender_is_an_outgoing_dynamic_property_of_email():
  sender = EmailAddress(email="sender@example.test", name="Sender")
  recipient = EmailAddress(email="recipient@example.test")
  email = Email(
    uid=1,
    message_id="message@example.test",
    subject="Graph direction",
    date=datetime.datetime(2026, 8, 7, tzinfo=datetime.UTC),
    body_text="The email is the subject of its from property.",
  )

  graph = EmailResolver.create_graph(email, sender, [recipient])

  assert graph.in_arcs == ()
  assert [arc.relation.content for arc in graph.out_arcs] == ["from", "to"]
  assert graph.out_arcs[0].to_graph.block.content == sender.model_dump_json()
