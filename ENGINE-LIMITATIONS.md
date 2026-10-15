# Engine defects and multiplayer: current evidence

This repository ships a compiled WebAssembly snapshot, not the C++ engine source or a reproducible engine build. Launcher fixes can change input, settings and asset delivery; they cannot by themselves repair engine animation or world simulation.

## Multiplayer / GTA Online

The current page starts the engine with `-nonetwork` and without Social Club. Removing that flag does not provide a server or synchronize a world. This project has no supported interface for reading/writing player entities, vehicles, ownership or mission state.

[FiveM](https://github.com/citizenfx/fivem) is a separate native framework. Its [installation](https://docs.fivem.net/docs/getting-started/installing-fivem/) uses a native GTA V installation; its client is not a drop-in browser WebAssembly module. Rockstar GTA Online and a community multiplayer implementation are different systems.

A genuine shared-world implementation needs:

1. A buildable engine integration exposing player/entity state, input and spawning, with stable entity IDs.
2. An authoritative server, transport, authentication and room lifecycle.
3. Ownership, interpolation, reconciliation and disconnect handling for players and vehicles.
4. Tests with two independent devices proving they see and interact with the same world, including reconnects and packet loss.

An invite link, chat room or position overlay would not meet that requirement. No multiplayer is claimed or supplied. Track the feature in [#17](https://github.com/alihammoud21/playgta5/issues/17).

## Minimap and vehicles

- [#13](https://github.com/alihammoud21/playgta5/issues/13): files verified, minimap roads missing on two device/browser paths; other audio works but several vehicle engines are silent. A generic autoplay or incomplete-download explanation does not fit all this evidence.
- [#16](https://github.com/alihammoud21/playgta5/issues/16): `memory access out of bounds` in `GFxValue::ObjectInterface::CreateEmptyMovieClip`, called from `CMiniMap_RenderThread::SetupContainers` / `CMiniMap::Init`. This identifies an engine/GFx initialization failure; it is not proof that 128 GB of RAM is insufficient.
- Vehicle entry delay, missing door/entry animation and backwards-facing driver have been reported in Chrome Free Roam on an RTX 3070. The user clarified that their minimap complaint is visual quality compared with the native game, not a completely broken minimap; this is separate from #13 and #16. They require a reproducible scene and comparison with controller disconnected to separate game state from input mapping.

No binary patches suppress these failures. Useful next evidence: exact launcher/URL, Story or Sandbox, location/vehicle, first exception stack, failed Network requests and a short reproduction recording. An engine maintainer needs the matching source/build to trace the GFx container lifetime, minimap assets, vehicle animation tasks and vehicle audio initialization.

## Mobile and performance

The support website is responsive. The engine still requires WebGPU, memory64, shared memory and sufficient device resources; experimental touch controls are implemented, with automated multi-touch/input-release tests but no phone gameplay validation. A phone displaying the launcher is not gameplay validation. Profiles change real existing engine settings, but no universal FPS increase is promised.

### MacBook Air performance profiles

The local server and static build apply Mac defaults of 1280×720, a 60 FPS cap, light graphics and shadows off. This avoids allocating native Retina-size render targets and uses the engine's existing low-memory worker and scene settings. Explicit URL options take precedence; an explicit `scale` also prevents the default `res` from masking it. The Windows 1 ms timer workaround now runs only on Windows. These changes do not rewrite the compiled engine or reserve additional RAM.

The support page offers a 1600×900 / 30 FPS light profile for a sharper image at a lower frame-rate target. If that is too demanding, use 1280×720 / 30 FPS. Switching is manual and reloads the game; save first. These profiles are not automatic performance detection and are not validated sustained 30/60 FPS claims.

For an M3 Air with 16 GB, compare the same loaded scene and driving route at 720p / 60 and 900p / 30, using one game tab and the same browser. Allow shader compilation and asset loading to settle, then observe several minutes of frame times, not only an average FPS counter. Record memory pressure and swap growth in Activity Monitor alongside browser/GPU use. macOS and other apps share the available memory; 16 GB alone neither proves sufficient headroom nor explains engine faults. Loading stalls, shader compilation and engine defects can still cause stutter at either cap. Sustained gameplay measurements remain pending.
