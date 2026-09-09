Customer engineering note after an Atlas Europe migration.

After the control-plane move, the service accepted 50 simultaneous imports for our tenant. It
queued the next request. Before the move we still observed the old cap.
