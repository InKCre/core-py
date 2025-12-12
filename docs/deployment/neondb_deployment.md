[Neon DB](https://neon.com) provides hosted PostgreSQL with PostgREST and more. 

## Scale to 0

NeonDB will automatically scales compute units to 0 when idle and which will results connec-
tion lost.

To resolve this, we can enable `pool_pre_ping` and so Sqlalchemy will check whether the conn-
ection is dead before
using it to avoid exception of connection lost. But for PostgreSQL notification listen, we 
will need to manually implement reconnect menhanism and this could exceeds Neon DB free plan
limits on compute hours. 