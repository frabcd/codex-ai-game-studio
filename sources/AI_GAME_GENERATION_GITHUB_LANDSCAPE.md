# AI Game Generation on GitHub: Repository Landscape

Snapshot: 2026-07-30

This is a broad, high-signal catalog of public GitHub repositories for AI-assisted or AI-generated games. It intentionally removes most forks, one-off student demos, SEO repositories, and tiny clones. It is not literally every repository on GitHub; GitHub search is continuously changing and many projects do not use consistent topics. Repository sections are the only source of repository counts and installable catalog records. **External references — pricing and licensing** is the explicit exception: it cites a standalone website, and entries there stay outside repository counts and outside the installable catalog.

Legend:

- **Production/tool**: usable in a real workflow today, subject to normal evaluation.
- **Research**: paper implementation, benchmark, or experimental model; often GPU-heavy.
- **Building block**: general technology that becomes game-relevant when placed in an asset or studio pipeline.
- **Index/skills**: curated links or agent instructions rather than a generator model.

Important: a repository's code license does not automatically cover its model weights, datasets, generated assets, game-engine SDKs, or third-party dependencies. Check all of them before commercial use.

## Best starting points

Stars below are an approximate GitHub snapshot from 2026-07-30, included only as a rough community signal.

| Need | Repository | Type | Approx. stars | Detected repo license | Why start here |
|---|---|---:|---:|---|---|
| Prompt to playable browser game | [leigest519/OpenGame](https://github.com/leigest519/OpenGame) | Research/tool | 2.8k | Apache-2.0 | End-to-end planning, code, assets, debugging, and visual/playability evaluation |
| Agentic studio roles and workflows | [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) | Skills | 23.5k | MIT | Large game-studio-style agent and workflow collection |
| Cross-engine game-development skills | [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) | Skills | 369 | Apache-2.0 | Engine, genre, systems, QA, and publishing skills |
| Unity editor automation | [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | Production/tool | 13.0k | MIT | Mature AI-to-Unity editor bridge with scene, asset, script, testing, and visual tools |
| Godot editor automation | [Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp) | Production/tool | 5.0k | MIT | Project execution, scene edits, screenshots, logs, and feedback loops |
| Unreal editor automation | [IvanMurzak/Unreal-MCP](https://github.com/IvanMurzak/Unreal-MCP) | Emerging tool | 17 | Apache-2.0 | New C++/.NET Unreal editor and runtime bridge with AI tools |
| Blender automation | [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) | Production/tool | 25.1k | MIT | Natural-language scene creation and manipulation in Blender |
| 3D asset generation | [microsoft/TRELLIS](https://github.com/microsoft/TRELLIS) | Research/tool | 13.3k | MIT | Strong image/text-to-3D meshes, Gaussians, and radiance fields |
| PBR-ready 3D assets | [Tencent-Hunyuan/Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | Research/tool | 3.8k | Custom/verify | Geometry plus production-oriented PBR materials |
| Broad Hunyuan 3D ecosystem | [Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) | Research/tool | 14.4k | Custom/verify | High-resolution shape and texture generation with a large ecosystem |
| Generated 3D worlds | [Tencent-Hunyuan/HY-World-2.0](https://github.com/Tencent-Hunyuan/HY-World-2.0) | Research | 2.4k | Custom/verify | Text/image/video to explorable mesh, 3DGS, point cloud, and engine-importable worlds |
| Real-time video world model | [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) | Research | 2.3k | MIT | Streaming interactive world model with long-horizon memory |
| Automatic rigging | [VAST-AI-Research/UniRig](https://github.com/VAST-AI-Research/UniRig) | Research/tool | 1.7k | MIT | Skeleton and skin-weight generation for varied 3D models |
| Static mesh to animation | [JarrentWu1031/AnimateAnyMesh](https://github.com/JarrentWu1031/AnimateAnyMesh) | Research/tool | 316 | Apache-2.0 | Text-driven animation with FBX/Alembic export |
| 2D sprite generation skill | [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) | Skills/tool | 3.5k | MIT | Sprite sheets, map art, transparent frames, and GIF workflows |
| Node-based asset generation | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | Building block | 122.9k | GPL-3.0 | Reproducible image, video, audio, and 3D generation graphs |
| AI playability testing | [Tencent/PlayCoder](https://github.com/Tencent/PlayCoder) | Research/tool | 42 | Verify | VLM-driven GUI testing and Play@k behavioral validation |
| Visual quality scoring | [chaofengc/IQA-PyTorch](https://github.com/chaofengc/IQA-PyTorch) | Building block | 3.3k | Verify | Large collection of image-quality metrics for automated asset review |
| Image/texture enhancement | [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | Production/tool | 36.3k | BSD-3-Clause | Practical restoration and upscaling |
| Game audio generation | [facebookresearch/audiocraft](https://github.com/facebookresearch/audiocraft) | Research/tool | 23.5k | MIT code; verify weights | MusicGen and AudioGen building blocks |

## 1. Master indexes, surveys, and agent skills

- [Yuan-ManX/ai-game-devtools](https://github.com/Yuan-ManX/ai-game-devtools) — **Index**. Broad game-AI directory covering LLMs, agents, world models, image, texture, shader, 3D, animation, video, audio, music, voice, and analytics.
- [simoninithomas/awesome-ai-tools-for-game-dev](https://github.com/simoninithomas/awesome-ai-tools-for-game-dev) — **Index**. Practical asset, texture, code, animation, voice, NPC, and game-design resources.
- [Anil-matcha/awesome-ai-game-generation](https://github.com/Anil-matcha/awesome-ai-game-generation) — **Index**. Newer list focused specifically on generated games.
- [matrix-agent/awesome-agentic-world-modeling](https://github.com/matrix-agent/awesome-agentic-world-modeling) — **Index**. World-model research including interactive game generation.
- [yyeboah/Awesome-Text-to-3D](https://github.com/yyeboah/Awesome-Text-to-3D) — **Index**. Text-to-3D research map.
- [llm-lab-org/Generative-AI-for-Character-Animation-Survey](https://github.com/llm-lab-org/Generative-AI-for-Character-Animation-Survey) — **Survey**. Generative character animation methods and repositories.
- [chaofengc/Awesome-Image-Quality-Assessment](https://github.com/chaofengc/Awesome-Image-Quality-Assessment) — **Index**. Visual quality and aesthetic assessment research.
- [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) — **Skills**. Portable game-development agent skills across Godot, Unity, Unreal, web engines, systems, genres, QA, and release.
- [thedivergentai/GD-Agentic-Skills](https://github.com/thedivergentai/GD-Agentic-Skills) — **Skills**. Large Godot-oriented skill and genre-blueprint library.
- [openai/plugins](https://github.com/openai/plugins/tree/main/plugins/game-studio) — **Skills/tooling**. Game-studio workflows including 2D sprite normalization and QA-oriented generation loops.
- [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) — **Skills**. Multi-role studio hierarchy, agents, and workflow skills.

Treat third-party skill repositories as executable instructions: inspect them, pin a commit, and review any scripts before giving an agent write access or secrets.

## 2. Prompt-to-game, game studios, and generated experiences

- [leigest519/OpenGame](https://github.com/leigest519/OpenGame) — **Research/tool**. Natural-language prompt to structured, implemented, tested browser game; includes GameCoder, reusable Game Skill, debugging, and OpenGame-Bench.
- [worldwonderer/novel-to-game](https://github.com/worldwonderer/novel-to-game) — **Skills/tool**. Seven-skill pipeline for turning a story or novel into a playable game.
- [SummerEngine/summer-engine-agent](https://github.com/SummerEngine/summer-engine-agent) — **Emerging tool**. AI-first game engine and skills framework.
- [Yuan-ManX/SparkLabs](https://github.com/Yuan-ManX/SparkLabs) — **Emerging tool**. AI-native game engine experiments.
- [codedpro/agentic-game-factory](https://github.com/codedpro/agentic-game-factory) — **Very early tool**. Agent pipeline for Godot mobile games, generated assets, QA, packaging, and store materials.
- [dinghuanghao/openword](https://github.com/dinghuanghao/openword) — **Generated experience**. Prompt-driven generative RPG world with rendered scenes and agent play.
- [Pasta-Devs/Marinara-Engine](https://github.com/Pasta-Devs/Marinara-Engine) — **Emerging tool**. Local roleplay/game engine with agents for world state, quests, combat, backgrounds, and narrative direction.
- [envy-ai/ai_rpg](https://github.com/envy-ai/ai_rpg) — **Tool/demo**. LLM game master with persistent world state and optional ComfyUI scene art.
- [a16z-infra/ai-town](https://github.com/a16z-infra/ai-town) — **Starter kit**. Deployable AI-character town with memory, chat, pixel assets, and optional generated music.
- [dweam-team/world-arcade](https://github.com/dweam-team/world-arcade) — **Tool**. Launcher for local generative games and world models.

## 3. Interactive world models and generated 3D worlds

### Video and action-conditioned worlds

- [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) — **Research**. Real-time streaming interactive world model with long-horizon memory.
- [Tencent-Hunyuan/HY-WorldPlay](https://github.com/Tencent-Hunyuan/HY-WorldPlay) — **Research**. HY-World 1.5 interactive world modeling with real-time latency and geometric consistency.
- [etched-ai/open-oasis](https://github.com/etched-ai/open-oasis) — **Research/tool**. Open inference code and weights for an action-conditioned Minecraft-like diffusion world model.
- [microsoft/mineworld](https://github.com/microsoft/mineworld) — **Research**. Real-time interactive Minecraft world model.
- [KlingAIResearch/GameFactory](https://github.com/KlingAIResearch/GameFactory) — **Research**. Action-controlled generative game video with open-domain style generalization.
- [GameGen-X/GameGen-X](https://github.com/GameGen-X/GameGen-X) — **Research**. Interactive open-world game video generation.
- [eloialonso/diamond](https://github.com/eloialonso/diamond) — **Research/tool**. Playable diffusion world models plus RL agents for Atari and CSGO experiments.
- [EnigmaLabsAI/multiverse](https://github.com/EnigmaLabsAI/multiverse) — **Research/demo**. Open multiplayer world-model experiment.

### Persistent geometry, scenes, and engine-importable worlds

- [Tencent-Hunyuan/HY-World-2.0](https://github.com/Tencent-Hunyuan/HY-World-2.0) — **Research**. Multimodal world generation and reconstruction to meshes, Gaussian splats, and point clouds.
- [Tencent-Hunyuan/HunyuanWorld-1.0](https://github.com/Tencent-Hunyuan/HunyuanWorld-1.0) — **Research**. Text/image to explorable semantically layered 3D worlds.
- [SkyworkAI/Matrix-3D](https://github.com/SkyworkAI/Matrix-3D) — **Research**. Large explorable 3D scene generation from text or a single image.
- [ZiYang-xie/WorldGen](https://github.com/ZiYang-xie/WorldGen) — **Research/tool**. Text/image to 3D scene in mesh or Gaussian-splat form.
- [HorizonRobotics/EmbodiedGen](https://github.com/HorizonRobotics/EmbodiedGen) — **Research/tool**. Text/image assets, textures, articulated objects, scenes, layout, and simulator export.
- [KovenYu/WonderWorld](https://github.com/KovenYu/WonderWorld) — **Research**. Interactive 3D scene generation from one image.
- [SensenGao/OneWorld](https://github.com/SensenGao/OneWorld) — **Research**. Unified representation autoencoder for 3D scene generation.
- [princeton-vl/infinigen](https://github.com/princeton-vl/infinigen) — **Building block**. Procedural photorealistic world generation with Blender; not prompt-to-game, but valuable for synthetic environments.

## 4. AI studio workflows and engine/editor control

### Unity

- [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) — **Production/tool**. Editor control, assets, scenes, scripts, tests, screenshots, and automation.
- [IvanMurzak/Unity-MCP](https://github.com/IvanMurzak/Unity-MCP) — **Production/tool**. Alternative Unity MCP with cloud/self-hosted server and extensible tools.
- [AnkleBreaker-Studio/unity-mcp-server](https://github.com/AnkleBreaker-Studio/unity-mcp-server) — **Emerging tool**. Large Unity/Hub tool surface.
- [AnkleBreaker-Studio/unity-mcp-plugin](https://github.com/AnkleBreaker-Studio/unity-mcp-plugin) — **Emerging tool**. Unity-side plugin paired with the server.
- [Unity-Technologies/ml-agents](https://github.com/Unity-Technologies/ml-agents) — **Production/research**. Train and evaluate intelligent game agents inside Unity.

### Godot

- [Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp) — **Production/tool**. Launch, run, debug, inspect, edit scenes, and capture feedback.
- [IvanMurzak/Godot-MCP](https://github.com/IvanMurzak/Godot-MCP) — **Production/tool**. Deep Godot editor and optional runtime integration.
- [tomyud1/godot-mcp](https://github.com/tomyud1/godot-mcp) — **Tool**. Editor plugin plus MCP server with project visualization.
- [fennaraOfficial/fennara-godot-ai](https://github.com/fennaraOfficial/fennara-godot-ai) — **Tool**. Native Godot AI chat plus MCP support.
- [edbeeching/godot_rl_agents](https://github.com/edbeeching/godot_rl_agents) — **Production/research**. Godot reinforcement-learning environments and agents.

### Unreal Engine

- [IvanMurzak/Unreal-MCP](https://github.com/IvanMurzak/Unreal-MCP) — **Emerging tool**. C++ editor plugin, .NET bridge, CLI, extensibility, and opt-in runtime control.
- [GenOrca/unreal-mcp](https://github.com/GenOrca/unreal-mcp) — **Emerging tool**. Actors, assets, materials, Blueprint graphs, behavior trees, and UMG through MCP.
- [Natfii/UnrealClaude](https://github.com/Natfii/UnrealClaude) — **Tool**. Unreal editor integration with version-aware documentation context.

### Blender, Aseprite, and shared DCC workflows

- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — **Production/tool**. AI-controlled modeling, scenes, and manipulation in Blender.
- [sakalond/StableGen](https://github.com/sakalond/StableGen) — **Production/tool**. Blender-based image/text-to-3D, texture generation, PBR baking, cleanup, and game-engine export.
- [carson-katri/dream-textures](https://github.com/carson-katri/dream-textures) — **Production/tool**. Stable Diffusion inside Blender for textures, concept art, backgrounds, scene projection, and animation restyling.
- [willibrandon/pixel-mcp](https://github.com/willibrandon/pixel-mcp) — **Production/tool**. AI-controlled Aseprite pixel drawing, palettes, animation, analysis, and spritesheet export.

## 5. 3D object, character, and mesh generation

### Modern high-value systems

- [Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) — **Research/tool**. High-resolution image/text-conditioned shapes and textures.
- [Tencent-Hunyuan/Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) — **Research/tool**. High-fidelity assets with PBR material generation.
- [microsoft/TRELLIS](https://github.com/microsoft/TRELLIS) — **Research/tool**. Structured 3D latents decoded as meshes, radiance fields, or Gaussians.
- [VAST-AI-Research/TripoSG](https://github.com/VAST-AI-Research/TripoSG) — **Research/tool**. High-fidelity image-to-3D shape synthesis.
- [stepfun-ai/Step1X-3D](https://github.com/stepfun-ai/Step1X-3D) — **Research/tool**. Controllable textured 3D assets with open inference and training components.
- [Stability-AI/stable-fast-3d](https://github.com/Stability-AI/stable-fast-3d) — **Research/tool**. Fast single-image mesh reconstruction with UV and material estimation.
- [VAST-AI-Research/TripoSR](https://github.com/VAST-AI-Research/TripoSR) — **Research/tool**. Lightweight, fast single-image reconstruction.
- [TencentARC/Pixal3D](https://github.com/TencentARC/Pixal3D) — **Research/tool**. Pixel-aligned image-to-3D with mesh output.
- [TencentARC/InstantMesh](https://github.com/TencentARC/InstantMesh) — **Research/tool**. Fast multiview-based single-image mesh generation.
- [AiuniAI/Unique3D](https://github.com/AiuniAI/Unique3D) — **Research/tool**. High-quality textured meshes from a single image.
- [xxlong0/Wonder3D](https://github.com/xxlong0/Wonder3D) — **Research/tool**. Cross-domain multiview diffusion for image-to-3D.
- [3DTopia/3DTopia-XL](https://github.com/3DTopia/3DTopia-XL) — **Research**. PBR asset generation through primitive diffusion.
- [3DTopia/LGM](https://github.com/3DTopia/LGM) — **Research/tool**. High-resolution multi-view Gaussian generation.
- [dreamgaussian/dreamgaussian](https://github.com/dreamgaussian/dreamgaussian) — **Research/tool**. Fast text/image-to-3D Gaussian generation.
- [SUDO-AI-3D/zero123plus](https://github.com/SUDO-AI-3D/zero123plus) — **Building block**. Consistent multiview diffusion used in many image-to-3D pipelines.

### Mesh representations, topology, and generation frameworks

- [buaacyw/MeshAnything](https://github.com/buaacyw/MeshAnything) — **Research/tool**. Converts geometry to artist-like low-face-count meshes.
- [buaacyw/MeshAnythingV2](https://github.com/buaacyw/MeshAnythingV2) — **Research/tool**. Follow-up mesh generation system.
- [nv-tlabs/LLaMA-Mesh](https://github.com/nv-tlabs/LLaMA-Mesh) — **Research**. Mesh generation and understanding through language-model tokenization.
- [Roblox/cube](https://github.com/Roblox/cube) — **Research/tool**. Roblox 3D foundation model and text-to-shape generation.
- [openai/shap-e](https://github.com/openai/shap-e) — **Research/tool**. Text/image-conditioned implicit 3D generation.
- [openai/point-e](https://github.com/openai/point-e) — **Research/tool**. Text/image-conditioned point-cloud generation.
- [threestudio-project/threestudio](https://github.com/threestudio-project/threestudio) — **Framework**. Unified modular framework for many text-to-3D methods.
- [ashawkey/stable-dreamfusion](https://github.com/ashawkey/stable-dreamfusion) — **Framework/research**. NeRF plus diffusion text/image-to-3D experimentation.
- [MrForExample/ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack) — **Production/tool**. ComfyUI nodes joining reconstruction, generation, cleanup, and preview workflows.

### Reconstruction and capture building blocks

- [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) — **Production/research**. NeRF and Gaussian-splat capture, training, viewing, and export tooling.
- [graphdeco-inria/gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting) — **Research/building block**. Foundational 3D Gaussian splatting implementation.

## 6. 3D textures, materials, lighting, and PBR

- [zzzyuqing/DreamMat](https://github.com/zzzyuqing/DreamMat) — **Research/tool**. Geometry- and light-aware PBR material generation.
- [VAST-AI-Research/SeqTex](https://github.com/VAST-AI-Research/SeqTex) — **Research**. End-to-end texture generation using video diffusion priors.
- [ashawkey/InTeX](https://github.com/ashawkey/InTeX) — **Research/tool**. Interactive depth-aware text-to-texture inpainting.
- [kaist-ami/Paint-it](https://github.com/kaist-ami/Paint-it) — **Research/tool**. Text-to-texture optimization with physically based rendering.
- [amtarr/ComfyUI-TextureAlchemy](https://github.com/amtarr/ComfyUI-TextureAlchemy) — **Tool**. ComfyUI nodes for albedo, normal, roughness, metallic, AO, height, curvature, tiling, and packing.
- [thegrayeminence/material-manager](https://github.com/thegrayeminence/material-manager) — **Tool/demo**. Browser PBR material generation and preview.
- [sakalond/StableGen](https://github.com/sakalond/StableGen) — **Production/tool**. Particularly useful when the output must be baked and exported from Blender.
- [Tencent-Hunyuan/Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) — **Research/tool**. Included again because PBR generation is one of its main differentiators.

## 7. Rigging, 3D animation, motion generation, and mocap

### Automatic rigging and animate-ready assets

- [VAST-AI-Research/UniRig](https://github.com/VAST-AI-Research/UniRig) — **Research/tool**. General skeleton and skin-weight prediction.
- [VAST-AI-Research/AniGen](https://github.com/VAST-AI-Research/AniGen) — **Research**. Single image to coherent mesh, skeleton, and skinning.
- [Seed3D/Puppeteer](https://github.com/Seed3D/Puppeteer) — **Research/tool**. Automatic rigging followed by video-guided animation.
- [JarrentWu1031/AnimateAnyMesh](https://github.com/JarrentWu1031/AnimateAnyMesh) — **Research/tool**. Text-driven animation of arbitrary static meshes.
- [facebookresearch/actionmesh](https://github.com/facebookresearch/actionmesh) — **Research/tool**. Video to animated mesh / 4D reconstruction.
- [Mesh2Motion/mesh2motion-app](https://github.com/Mesh2Motion/mesh2motion-app) — **Production/tool**. Web-based skeleton assignment and animation export; useful even when the source mesh is AI-generated.

### Text-to-motion and animation intelligence

- [OpenMotionLab/MotionGPT](https://github.com/OpenMotionLab/MotionGPT) — **Research/tool**. Text-to-motion, motion captioning, prediction, and in-betweening.
- [EricGuo5513/momask-codes](https://github.com/EricGuo5513/momask-codes) — **Research/tool**. High-quality masked-model 3D human motion generation.
- [facebookresearch/ai4animationpy](https://github.com/facebookresearch/ai4animationpy) — **Framework**. Neural character-animation, mocap processing, training, and inference.

### Motion capture and pose

- [xianfei/SysMocap](https://github.com/xianfei/SysMocap) — **Production/tool**. Real-time monocular mocap and avatar animation.
- [open-mmlab/mmpose](https://github.com/open-mmlab/mmpose) — **Building block**. Large pose-estimation toolbox for animation capture pipelines.

## 8. 2D sprites, pixel art, tiles, concept art, and consistency

### Game-focused generation and agent workflows

- [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) — **Skills/tool**. Prompt-to-sprite sheets, maps, transparent frames, and animated previews.
- [EYamanS/texel-studio](https://github.com/EYamanS/texel-studio) — **Emerging tool**. Tool-using pixel-art agent that paints rather than relying only on diffusion.
- [GAlbanese09/spritebrew](https://github.com/GAlbanese09/spritebrew) — **Production/tool**. Text-to-sprite, animation, slicing, editing, and export to Unity, Godot, GameMaker, and RPG Maker.
- [blendi-remade/sprite-sheet-creator](https://github.com/blendi-remade/sprite-sheet-creator) — **Tool**. Prompt/image to characters, animations, maps, and parallax backgrounds through hosted model APIs.
- [charmed-ai/tilemapgen](https://github.com/charmed-ai/tilemapgen) — **Research/tool**. Stable-Diffusion-assisted isometric dungeon tile and tilemap generation.
- [ece1786-2023/Animyth](https://github.com/ece1786-2023/Animyth) — **Prototype**. Text-to-spritesheet workflow using Stable Diffusion and ControlNet.
- [willibrandon/pixel-mcp](https://github.com/willibrandon/pixel-mcp) — **Production/tool**. Natural-language pixel drawing and animation with deterministic inspection/export operations.

### General image-generation building blocks

- [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) — **Production/building block**. Node graphs for reproducible asset pipelines and batch generation.
- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) — **Production/building block**. Large Stable Diffusion web UI and extension ecosystem.
- [lllyasviel/ControlNet](https://github.com/lllyasviel/ControlNet) — **Building block**. Pose, edge, depth, segmentation, and layout conditioning.
- [TencentARC/PhotoMaker](https://github.com/TencentARC/PhotoMaker) — **Building block**. Consistent personalized characters from reference images.
- [instantX-research/InstantID](https://github.com/instantX-research/InstantID) — **Building block**. Identity preservation from a single reference; review InsightFace and weight restrictions.
- [ToTheBeginning/PuLID](https://github.com/ToTheBeginning/PuLID) — **Building block**. Tuning-free identity customization.
- [facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything) — **Building block**. Asset masking and segmentation.
- [danielgatis/rembg](https://github.com/danielgatis/rembg) — **Production/building block**. Background removal for sprites, icons, and concept assets.

### Pixel editors and map tools used to repair AI output

- [aseprite/aseprite](https://github.com/aseprite/aseprite) — Animated pixel-art editor; source-available terms require attention.
- [Orama-Interactive/Pixelorama](https://github.com/Orama-Interactive/Pixelorama) — MIT-licensed pixel-art, animation, and tileset editor.
- [mapeditor/tiled](https://github.com/mapeditor/tiled) — Tilemap and level editor for arranging generated tiles and adding collision/object metadata.

## 9. Procedural content, level generation, terrain, and design

- [shyamsn97/mario-gpt](https://github.com/shyamsn97/mario-gpt) — **Research/tool**. Text-conditioned Mario level generation with a language model.
- [schrum2/MarioDiffusion](https://github.com/schrum2/MarioDiffusion) — **Research/tool**. Text-to-playable Mario level scenes using diffusion, with GUI and automated play checks.
- [amidos2006/gym-pcgrl](https://github.com/amidos2006/gym-pcgrl) — **Research/framework**. Reinforcement learning for procedural level generation.
- [openai/procgen](https://github.com/openai/procgen) — **Research/benchmark**. Fast procedurally generated game-like environments for generalization testing.
- [xandergos/terrain-diffusion](https://github.com/xandergos/terrain-diffusion) — **Research/tool**. Learned infinite, deterministic, random-access terrain generation.
- [princeton-vl/infinigen](https://github.com/princeton-vl/infinigen) — **Production/research**. Procedural natural environments and synthetic worlds.
- [microsoft/TextWorld](https://github.com/microsoft/TextWorld) — **Research/framework**. Generate text-game worlds, quests, and environments for agent research.
- [THU-LYJ-Lab/T3Bench](https://github.com/THU-LYJ-Lab/T3Bench) — **Benchmark**. Text-to-3D quality and prompt-alignment evaluation; useful for choosing an asset generator.

## 10. NPCs, dialogue, quests, narrative, and game masters

- [undreamai/LLMUnity](https://github.com/undreamai/LLMUnity) — **Production/tool**. Local or remote LLM characters, RAG, and Unity integration.
- [Adriankhl/godot-llm](https://github.com/Adriankhl/godot-llm) — **Production/tool**. Local LLM, multimodal inference, embeddings, and vector search in Godot.
- [aws-solutions-library-samples/guidance-for-dynamic-game-npc-dialogue-on-aws](https://github.com/aws-solutions-library-samples/guidance-for-dynamic-game-npc-dialogue-on-aws) — **Reference architecture**. Unreal MetaHuman, RAG, LLMOps, voice, and viseme/lip-sync pipeline.
- [AkiKurisu/Next-Gen-Dialogue](https://github.com/AkiKurisu/Next-Gen-Dialogue) — **Tool**. Unity visual dialogue editor with AIGC baking, localization, and VITS speech.
- [MinLL/SkyrimNet-GamePlugin](https://github.com/MinLL/SkyrimNet-GamePlugin) — **Production/mod**. Conversational, memory-bearing, voiced Skyrim NPCs.
- [a16z-infra/ai-town](https://github.com/a16z-infra/ai-town) — **Starter kit**. Multi-agent social simulation and customizable characters.
- [envy-ai/ai_rpg](https://github.com/envy-ai/ai_rpg) — **Tool/demo**. Structured world, inventory, and game-master state with generated artwork.
- [Pasta-Devs/Marinara-Engine](https://github.com/Pasta-Devs/Marinara-Engine) — **Emerging tool**. Game-master, party, quest, combat, and visual-scene agents.

## 11. Audio, sound effects, music, speech, and voices

- [facebookresearch/audiocraft](https://github.com/facebookresearch/audiocraft) — **Research/tool**. MusicGen and AudioGen for music and sound effects.
- [haoheliu/AudioLDM2](https://github.com/haoheliu/AudioLDM2) — **Research/tool**. Text-to-audio, music, speech, and sound-effect generation.
- [declare-lab/tango](https://github.com/declare-lab/tango) — **Research/tool**. Text-to-audio diffusion with released checkpoints.
- [Tencent-Hunyuan/HunyuanVideo-Foley](https://github.com/Tencent-Hunyuan/HunyuanVideo-Foley) — **Research/tool**. Video-conditioned Foley sound generation.
- [gabotechs/MusicGPT](https://github.com/gabotechs/MusicGPT) — **Production/tool**. Local natural-language music generation with packaged binaries.
- [myshell-ai/OpenVoice](https://github.com/myshell-ai/OpenVoice) — **Research/tool**. Voice cloning and style control.
- [coqui-ai/TTS](https://github.com/coqui-ai/TTS) — **Production/building block**. Text-to-speech training and inference ecosystem.
- [RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) — **Production/tool**. Voice conversion; obtain clear rights and consent for all voices.

## 12. Automated playtesting, gameplay agents, and functional QA

- [Tencent/PlayCoder](https://github.com/Tencent/PlayCoder) — **Research/tool**. Executes, unit-tests, visually plays, diagnoses, and refines generated GUI/game code.
- [leigest519/OpenGame](https://github.com/leigest519/OpenGame) — **Research/tool**. OpenGame-Bench evaluates build health, visual usability, and prompt/intent alignment.
- [lmgame-org/GamingAgent](https://github.com/lmgame-org/GamingAgent) — **Research/tool**. Standardized LLM/VLM agents and evaluation across multiple games.
- [BAAI-Agents/Cradle](https://github.com/BAAI-Agents/Cradle) — **Research/framework**. General computer-control agents demonstrated in complex games.
- [balrog-ai/BALROG](https://github.com/balrog-ai/BALROG) — **Research/benchmark**. Agent capabilities in challenging games.
- [GAIR-NLP/AgencyBench](https://github.com/GAIR-NLP/AgencyBench) — **Benchmark**. Long-horizon agents with game-development tasks and visual/rule-based grading.
- [chasemetoyer/gameplay-vision-llm](https://github.com/chasemetoyer/gameplay-vision-llm) — **Emerging tool**. Gameplay-video understanding, glitch detection, visual unit tests, and bug reports.
- [Farama-Foundation/ViZDoom](https://github.com/Farama-Foundation/ViZDoom) — **Research/framework**. Fast visual-agent testing in Doom with labels, depth, geometry, and audio access.
- [Unity-Technologies/ml-agents](https://github.com/Unity-Technologies/ml-agents) — **Production/research**. Train bots to explore balance, behavior, navigation, and edge cases in Unity.
- [edbeeching/godot_rl_agents](https://github.com/edbeeching/godot_rl_agents) — **Production/research**. Equivalent RL and agent experimentation for Godot.

## 13. Visual quality, aesthetic scoring, and generated-asset review

- [chaofengc/IQA-PyTorch](https://github.com/chaofengc/IQA-PyTorch) — **Production/research**. Unified full-reference and no-reference image-quality metrics.
- [Q-Future/Q-Align](https://github.com/Q-Future/Q-Align) — **Research/tool**. Multimodal-model visual quality and aesthetic scoring.
- [zai-org/ImageReward](https://github.com/zai-org/ImageReward) — **Research/tool**. Ranks text-to-image results against prompt and preference signals.
- [yuvalkirstain/PickScore](https://github.com/yuvalkirstain/PickScore) — **Research/tool**. Human-preference-based image ranking.
- [XPixelGroup/DepictQA](https://github.com/XPixelGroup/DepictQA) — **Research/tool**. Vision-language image-quality assessment with explanations.
- [LAION-AI/aesthetic-predictor](https://github.com/LAION-AI/aesthetic-predictor) — **Building block**. Lightweight aesthetic scoring.
- [idealo/image-quality-assessment](https://github.com/idealo/image-quality-assessment) — **Archived reference**. Older NIMA aesthetic and technical quality predictor.
- [THU-LYJ-Lab/T3Bench](https://github.com/THU-LYJ-Lab/T3Bench) — **Benchmark**. Text-to-3D quality and alignment evaluation.

No single metric can validate game art. Combine technical constraints, prompt/reference similarity, temporal consistency, engine screenshots, and human art direction.

## 14. Quality enhancement, cleanup, restoration, and interpolation

- [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) — **Production/tool**. General image restoration and upscaling.
- [Fanghua-Yu/SUPIR](https://github.com/Fanghua-Yu/SUPIR) — **Research/tool**. Prompt-aware image restoration and upscale.
- [XPixelGroup/HAT](https://github.com/XPixelGroup/HAT) — **Research/tool**. High-quality transformer image super-resolution.
- [JingyunLiang/SwinIR](https://github.com/JingyunLiang/SwinIR) — **Research/tool**. Super-resolution, denoising, and JPEG artifact reduction.
- [hzwer/Practical-RIFE](https://github.com/hzwer/Practical-RIFE) — **Production/tool**. Frame interpolation for animation/video smoothing.
- [TencentARC/GFPGAN](https://github.com/TencentARC/GFPGAN) — **Production/tool**. Face restoration for character portraits and cinematics.
- [sczhou/CodeFormer](https://github.com/sczhou/CodeFormer) — **Production/tool**. Face restoration with quality/fidelity control.
- [lllyasviel/IC-Light](https://github.com/lllyasviel/IC-Light) — **Building block**. Relighting for more consistent concept art and presentation renders.
- [danielgatis/rembg](https://github.com/danielgatis/rembg) — **Production/tool**. Background cleanup and transparent-asset preparation.
- [facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything) — **Building block**. Object masks for cleanup, inpainting, recoloring, and asset extraction.

## 15. Non-AI technical gates worth adding to an AI asset pipeline

These are not generators, but they catch problems that visual AI judges often miss.

- [KhronosGroup/glTF-Validator](https://github.com/KhronosGroup/glTF-Validator) — glTF structural and specification validation.
- [zeux/meshoptimizer](https://github.com/zeux/meshoptimizer) — Mesh simplification, vertex/index optimization, LOD, and compression.
- [google/draco](https://github.com/google/draco) — Mesh and point-cloud compression.
- [assimp/assimp](https://github.com/assimp/assimp) — Import/export checks across many 3D formats.
- [KhronosGroup/KTX-Software](https://github.com/KhronosGroup/KTX-Software) — GPU texture validation, conversion, and compression.
- [microsoft/playwright](https://github.com/microsoft/playwright) — Browser-game interaction, screenshot, and regression testing.
- [garris/BackstopJS](https://github.com/garris/BackstopJS) — Screenshot-based visual regression for web games and tools.

## Recommended stacks

### Fast 2D/browser game generation

1. OpenGame or a conventional coding agent for the playable game.
2. Agent Sprite Forge, SpriteBrew, or a ComfyUI + ControlNet workflow for art.
3. Aseprite MCP or Pixelorama for deterministic repair and consistent exports.
4. PlayCoder/OpenGame-Bench plus Playwright for functional and visual checks.
5. IQA-PyTorch plus a human review rubric for final art selection.

### Unity 3D asset pipeline

1. CoplayDev Unity MCP for editor control and tests.
2. Hunyuan3D-2.1, TRELLIS, or TripoSG for source meshes.
3. MeshAnything for topology experiments; inspect collision and LOD manually.
4. UniRig or Puppeteer for rigging; MotionGPT/MoMask for motion candidates.
5. Blender MCP or StableGen for UV, PBR, bake, decimation, and export.
6. glTF Validator, meshoptimizer, Unity tests, screenshots, and human sign-off.

### Godot 2D/3D workflow

1. Coding-Solo Godot MCP or Fennara for editor feedback.
2. Agent Sprite Forge / pixel-mcp for 2D, or TRELLIS / Hunyuan3D for 3D.
3. Godot RL Agents for repeatable behavior and playtest environments.
4. Engine screenshots plus PlayCoder-style VLM checks and deterministic assertions.

### Unreal world-building workflow

1. Unreal MCP or UnrealClaude for editor and project operations.
2. HY-World 2.0, HunyuanWorld, WorldGen, or Infinigen for environment sources.
3. Hunyuan3D/TRELLIS plus UniRig for individual characters and props.
4. Blender/StableGen for final optimization and PBR bake.
5. Unreal automation tests, packaged-build smoke tests, screenshot comparison, and gameplay capture review.

### Interactive world-model research

1. Matrix-Game or HY-WorldPlay for recent streaming systems.
2. Open Oasis, MineWorld, DIAMOND, and GameFactory as reproducible baselines.
3. World Arcade as a convenient launcher where supported.
4. GamingAgent/BALROG-style evaluation for controllability and long-horizon behavior.

## Minimum quality gate for generated game assets

1. **Rights**: code, weights, dataset, source-reference, voice, and generated-output terms are acceptable.
2. **Technical validity**: format parses; transforms, scale, axes, normals, UVs, materials, bones, animation clips, LODs, and collision are valid.
3. **Visual consistency**: silhouette, palette, proportions, identity, texel density, seams, and lighting remain consistent across views/frames.
4. **Runtime budget**: triangle count, texture memory, shader complexity, draw calls, animation cost, and loading time meet the target platform.
5. **Playability**: the asset behaves correctly in an actual build, not only in a turntable render.
6. **Regression evidence**: store engine screenshots/video, automated results, generation settings, model/weight versions, and source commit.
7. **Human approval**: art direction, fun, readability, originality, and legal risk still require a responsible reviewer.

## External references — pricing and licensing

These entries are standalone websites. They are excluded from repository counts and installable catalog records.

- [RespawnStack](https://respawnstack.com/) — **External reference**. Free-to-read directory of AI game-tool pricing, commercial-use terms, and output ownership, with dated vendor quotes where verified and explicit unverified entries. Advertising/affiliate-supported; recheck original vendor terms before commercial use.
