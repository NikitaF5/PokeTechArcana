# Server compatibility fixes

## Stellar Blue interactions on Cobblemon 1.8.0

`stellar-blue-interactions-fix` overrides two files from Cobblemon Stellar Blue
1.5:

- `data/cobblemon/pokemon_interactions/spudlett.json`
- `data/cobblemon/pokemon_interactions/spudtrio.json`

Both upstream files use Cobblemon's `chance` requirement. Cobblemon 1.8.0 can
read this requirement on the server, but serializes its internal MoLang syntax
tree when synchronizing interactions to a client. The client accepts only a
primitive string or an array and disconnects with `Invalid expression JSON`.

The compatibility pack disables only the bone meal interactions for Spudlett
and Spudtrio. Species, models, starters, spawn pools, dialogues, moves and all
other Stellar Blue content remain enabled.

Build the deployment archive from inside the fix directory so `pack.mcmeta` is
at the ZIP root. Install it after the original Stellar Blue datapack.
