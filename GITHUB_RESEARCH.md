# GitHub Research: Point Cloud to CAD Reverse Engineering

Дата анализа: 2026-05-17.

Цель: найти на GitHub репозитории, которые уже решали близкую задачу reverse engineering CAD из 3D point cloud, и понять, что из этого реально полезно для нашего проекта на базе Point2CAD.

## Short Verdict

Есть несколько разных классов решений, и они не взаимозаменяемы:

1. **Surface/topology reconstruction**: ближе всего к текущему Point2CAD. Восстанавливает поверхности, ребра, углы, но обычно требует сегментированное облако точек.
2. **CAD code reconstruction**: point cloud превращается в CadQuery/Python-код. Это ближе к редактируемому CAD и STEP-export через CAD kernel, но точность и стабильность зависят от модели.
3. **B-Rep / chain-complex reconstruction**: пытается восстановить топологическую структуру B-Rep напрямую. Перспективно, но тяжелее по зависимостям и интеграции.
4. **Primitive segmentation/fitting**: не дает CAD целиком, но закрывает ключевой bottleneck текущего Point2CAD: получение `surface_id` и параметров примитивов из raw point cloud.
5. **CSG reconstruction**: восстанавливает дерево boolean-примитивов, полезно для редактируемости, но не равно полноценному B-Rep CAD.

Практический вывод: для нашего текущего направления самый разумный первый маршрут:

- оставить `prs-eth/point2cad` как базу для surface/topology reconstruction;
- добавить фронтенд-сегментацию через `Hippogriff/parsenet-codebase`, `SimingYan/HPNet` или `lingxiaoli94/SPFN`;
- параллельно проверить `filaPro/cad-recode` и `col14m/cadrille`, если нам нужен именно редактируемый CadQuery/STEP, а не только mesh + topology.

## Search Scope

Искал через GitHub Search, `gh search repos`, `gh repo view`, GitHub README и web search.

Основные запросы:

- `point cloud CAD reverse engineering`
- `CAD reconstruction B-Rep point cloud`
- `point cloud CadQuery CAD`
- `primitive fitting point clouds CAD`
- `HPNet primitive segmentation`
- `ParSeNet point cloud`
- `SPFN primitive fitting`
- `ComplexGen CAD`
- `Cadrille CAD point cloud`
- `inverse CSG point cloud CAD reconstruction`

Метаданные ниже сняты через `gh` на дату анализа. Звезды/форки могут быстро измениться.

## Top Candidates

| Repo                                                                            | Stars | What It Solves                         | Input                                     | Output                                      | Fit For Us                               | Main Caveat                                 |
| ------------------------------------------------------------------------------- | ----: | -------------------------------------- | ----------------------------------------- | ------------------------------------------- | ---------------------------------------- | ------------------------------------------- |
| [prs-eth/point2cad](https://github.com/prs-eth/point2cad)                       |   431 | CAD surface/topology reconstruction    | annotated point cloud: `x y z surface_id` | unclipped/clipped mesh + edges/corners JSON | Current baseline                         | raw point cloud segmentation is external    |
| [filaPro/cad-recode](https://github.com/filaPro/cad-recode)                     |   234 | point cloud to CAD code                | point cloud                               | CadQuery Python code                        | Strong candidate for editable CAD route  | LLM-based, demo-oriented repo               |
| [col14m/cadrille](https://github.com/col14m/cadrille)                           |   143 | multimodal CAD reconstruction          | point cloud / image / text                | CadQuery Python code                        | Strong modern candidate                  | RL fine-tuning code not provided            |
| [guohaoxiang/ComplexGen](https://github.com/guohaoxiang/ComplexGen)             |   125 | B-Rep chain complex reconstruction     | point cloud + normals                     | vertices/edges/patches, final JSON/complex  | Best B-Rep-style research candidate      | heavy env, Gurobi/Mosek, Windows refinement |
| [mikacuy/point2cyl](https://github.com/mikacuy/point2cyl)                       |    65 | point cloud to extrusion cylinders     | raw point cloud                           | sketch/extrusion-cylinder decomposition     | Good for sketch/extrude mechanical parts | limited representation                      |
| [Hippogriff/parsenet-codebase](https://github.com/Hippogriff/parsenet-codebase) |   144 | parametric surface patch decomposition | point cloud, optionally normals           | segments, primitive/spline fits             | Directly useful before Point2CAD         | old research stack                          |
| [SimingYan/HPNet](https://github.com/SimingYan/HPNet)                           |    75 | primitive segmentation                 | point cloud                               | primitive segments/parameters               | Good `surface_id` generator candidate    | trained/evaluated on ABCParts               |
| [lingxiaoli94/SPFN](https://github.com/lingxiaoli94/SPFN)                       |   185 | supervised primitive fitting           | point cloud                               | membership/type/normal/primitive params     | Good classical-DL bridge                 | TensorFlow 1 era                            |
| [erictuanle/CPFN](https://github.com/erictuanle/CPFN)                           |    24 | high-res primitive fitting             | high-res point cloud                      | global/local primitive detections           | Useful for dense scans                   | more complex training pipeline              |
| [kacperkan/ucsgnet](https://github.com/kacperkan/ucsgnet)                       |    45 | CSG tree discovery                     | point/voxel-like data                     | CSG tree                                    | Alternative editable representation      | not B-Rep, not industrial CAD out of box    |
| [yijiangh/InverseCSG](https://github.com/yijiangh/InverseCSG)                   |    71 | 3D model to CSG tree                   | 3D model/examples                         | OpenSCAD-like CSG solution                  | Useful algorithmic reference             | older, heavy synthesis dependency           |

## Detailed Notes

### 1. prs-eth/point2cad

Repository: <https://github.com/prs-eth/point2cad>

This is the repo we cloned and are reading. It is directly aligned with our task: reconstructing CAD-like surfaces, edges, and corners from point clouds.

What it actually expects:

- input is not just raw `xyz`;
- input is `x y z surface_id`;
- segmentation/annotation must be done by another model such as ParseNet or HPNet.

Output:

- `out/unclipped/mesh.ply`
- `out/clipped/mesh.ply`
- `out/topo/topo.json`

Strengths:

- close to our target;
- has Docker path;
- reconstructs both surfaces and topology;
- combines analytic primitives with INR spline surfaces.

Weaknesses:

- not end-to-end raw scan to CAD;
- output is not a native STEP/B-Rep solid;
- topology is extracted from mesh intersections, so downstream CAD export will need another layer.

Note: current repo metadata says Apache-2.0, while the README in this checkout mentions non-commercial CC-BY-NC terms. License must be checked before any commercial use.

### 2. filaPro/cad-recode

Repository: <https://github.com/filaPro/cad-recode>

CAD-Recode is one of the most relevant newer solutions. It transforms point cloud input into CadQuery Python code. That is a big difference from Point2CAD: instead of only surfaces/topology, it tries to recover an editable CAD program.

Output direction:

- point cloud -> Python/CadQuery code -> CAD model;
- from CadQuery we can potentially export STEP.

Strengths:

- direct point cloud to editable CAD-code route;
- provides Hugging Face models and datasets;
- repo claims strong results on DeepCAD, Fusion360, CC3D;
- much closer to "usable CAD" than mesh-only reconstruction.

Weaknesses:

- LLM decoder means failures may be semantic/programmatic, not just geometric;
- repo is centered on an inference demo;
- for real scans, robustness still needs to be tested;
- output may be plausible CAD code rather than exact measured reverse engineering.

Best use for us:

- benchmark on our sample point clouds;
- compare generated CadQuery/STEP against Point2CAD mesh/topology;
- possibly use it as a separate "CAD program recovery" branch.

### 3. col14m/cadrille

Repository: <https://github.com/col14m/cadrille>

Cadrille is a follow-up/neighbor to CAD-Recode. It is multimodal: point cloud, image, and text inputs can condition CAD reconstruction. Current GitHub metadata marks it as ICLR 2026.

Output:

- CadQuery code.

Strengths:

- supports point-cloud-only inference mode;
- can use image/text as extra conditioning if we have renders or user descriptions;
- repository provides SFT/RL model links;
- current and active compared with older primitive fitting repos.

Weaknesses:

- RL fine-tuning code is not released;
- still CadQuery-code generation, not guaranteed exact B-Rep recovery;
- will need practical testing on noisy, partial, real scans.

Best use for us:

- evaluate as the modern LLM/CadQuery route;
- useful if the target is "editable generated model" rather than exact surface reverse engineering.

### 4. guohaoxiang/ComplexGen

Repository: <https://github.com/guohaoxiang/ComplexGen>

ComplexGen is the strongest B-Rep-style research candidate I found. It treats CAD reconstruction as detection of vertices, edges, surface patches, and their relationships as a chain complex.

Output:

- predicted primitives and relations;
- `.complex` visualizable files;
- geometric refinement JSON as final output.

Strengths:

- explicitly models B-Rep-like topology;
- starts from point cloud processing;
- includes neural prediction plus global optimization constraints;
- better conceptual match for "CAD topology" than pure mesh reconstruction.

Weaknesses:

- environment is heavy;
- extraction needs optimization solvers like Gurobi/Mosek;
- geometric refinement is Windows-oriented in the README;
- training from scratch is expensive;
- not a simple library to drop into our current code.

Best use for us:

- use as a reference architecture for topology recovery;
- run only if we want a serious B-Rep reconstruction branch and can tolerate the dependency stack.

### 5. mikacuy/point2cyl

Repository: <https://github.com/mikacuy/point2cyl>

Point2Cyl reconstructs objects as extrusion cylinders: a 2D sketch, an extrusion axis/range, and boolean combinations.

Strengths:

- input is raw point cloud;
- output representation is closer to CAD design intent than simple primitive patches;
- has pretrained models;
- targets DeepCAD/Fusion-style mechanical parts.

Weaknesses:

- representation is narrower than general CAD/B-Rep;
- not aimed at arbitrary freeform surfaces;
- code is older and research-oriented.

Best use for us:

- good for parts dominated by extrusions, holes, cylinders, brackets;
- bad for arbitrary NURBS/freeform reconstruction.

### 6. Hippogriff/parsenet-codebase

Repository: <https://github.com/Hippogriff/parsenet-codebase>

ParSeNet decomposes point clouds into parametric surface patches, including primitives and B-spline patches. Point2CAD explicitly names ParseNet as a way to get surface clusters.

Strengths:

- directly relevant to generating `surface_id`;
- includes point-only and point+normal training/testing modes;
- fits B-spline patches, not only planes/cylinders.

Weaknesses:

- research stack from 2020;
- training can require multiple GPUs;
- integration will need conversion from ParSeNet outputs into Point2CAD `.xyzc` format.

Best use for us:

- first serious candidate for raw cloud -> annotated `.xyzc`.

### 7. SimingYan/HPNet

Repository: <https://github.com/SimingYan/HPNet>

HPNet is primitive segmentation using hybrid representations. It provides preprocessed ABCParts data and pretrained models.

Strengths:

- directly addresses primitive segmentation;
- likely useful for creating surface labels before Point2CAD;
- more recent than SPFN and directly mentioned by Point2CAD README as an option.

Weaknesses:

- dataset assumptions matter;
- not an end-to-end CAD reconstructor;
- output conversion into our pipeline must be written.

Best use for us:

- compare against ParseNet for generating `surface_id`.

### 8. lingxiaoli94/SPFN

Repository: <https://github.com/lingxiaoli94/SPFN>

SPFN predicts per-point properties and uses differentiable model estimation to compute primitive type and parameters. It was an important baseline before ParSeNet/HPNet/CPFN.

Strengths:

- outputs per-point membership/type/normals and primitive parameters;
- can test with only input points;
- strong baseline for analytic primitive fitting.

Weaknesses:

- TensorFlow 1.10 / Python 3.6 era;
- probably painful to integrate directly;
- less expressive than ParSeNet for spline patches.

Best use for us:

- baseline or fallback for analytic primitive segmentation.

### 9. erictuanle/CPFN

Repository: <https://github.com/erictuanle/CPFN>

CPFN improves primitive fitting on high-resolution point clouds by combining global and local primitive detection.

Strengths:

- specifically targets high-resolution scans;
- improves detection of fine-scale primitives;
- relevant if our scans are dense and contain small features.

Weaknesses:

- more complex preprocessing/training;
- not a direct CAD output;
- relies on SPFN-style components.

Best use for us:

- consider after ParSeNet/HPNet if high-res fine details are a bottleneck.

### 10. kacperkan/ucsgnet

Repository: <https://github.com/kacperkan/ucsgnet>

UCSG-Net discovers Constructive Solid Geometry trees in an unsupervised way.

Strengths:

- output is editable in principle;
- CSG tree can capture boolean design intent;
- includes pretrained models and experiment pipeline.

Weaknesses:

- CSG is not the same as B-Rep or feature history;
- may work best on shapes expressible by simple primitives;
- integration into CAD kernels would be separate work.

Best use for us:

- reference for an alternative representation: point cloud -> boolean CAD-like program.

### 11. yijiangh/InverseCSG

Repository: <https://github.com/yijiangh/InverseCSG>

InverseCSG is older, but relevant because it converts 3D models into CSG trees. It includes example CAD models and OpenSCAD-like output.

Strengths:

- actual conversion to symbolic CSG representation;
- algorithmic, not just neural;
- useful reference for program synthesis style reverse engineering.

Weaknesses:

- older stack;
- dependency on Sketch/program synthesis tooling;
- not a convenient modern point-cloud-to-CAD pipeline.

Best use for us:

- idea/reference only, not the first implementation target.

## Lower-Confidence / Prototype Repositories

### ThahseenAS-sadiq/pointCloud2CAD

Repository: <https://github.com/ThahseenAS-sadiq/pointCloud2CAD>

Claims a point-cloud-to-STEP pipeline using Open3D, primitive fitting and pythonOCC. It has no stars/forks at the time of analysis and reads like a small project scaffold.

Potential value:

- useful as a simple pythonOCC pipeline sketch;
- shows expected stages: denoise, downsample, segment, fit, build STEP.

Risk:

- not a validated research implementation;
- likely narrow assumptions.

### dalidesign10-dev/scan-to-cad

Repository: <https://github.com/dalidesign10-dev/scan-to-cad>

This is an application prototype with Electron/React/FastAPI, Open3D/trimesh/OCC, and optional Point2Cyl. The README is honest: it produces scan-derived polyhedral B-Rep and has manual workflows, but not true analytic CAD design-intent reconstruction yet.

Potential value:

- practical OCC/export workflow inspiration;
- UI architecture for manual reverse engineering;
- explicitly separates cleanup, primitive fitting, cage extraction, fillet/chamfer/STEP export.

Risk:

- zero stars/forks;
- Windows-specific/hardcoded paths;
- not a proven reconstruction algorithm.

## Repos/Papers That Are Interesting But Not Directly Usable Yet

### CAD-MLLM/CAD-MLLM

Repository: <https://github.com/CAD-MLLM/CAD-MLLM>

Important as a recent multimodal CAD generation project and dataset/metrics source. But the README says inference and training code are still TODO. The useful immediate part is their evaluation thinking: metrics such as segment error, dangling edge length, self-intersection ratio and flux enclosure error.

Use for us:

- borrow evaluation ideas;
- do not rely on it as a working point-cloud-to-CAD implementation today.

### Blice0415/P2CADNet

Repository: <https://github.com/Blice0415/P2CADNet>

The paper claims an end-to-end point-cloud-to-parametric-CAD model, but the GitHub repo currently only has a README saying code will be released after acceptance. Treat as not usable.

### CAD-SIGNet / TransCAD

These are relevant papers for point-cloud-to-CAD-language/design-history inference, but I did not find a usable official GitHub repo during this pass. Keep them in literature watch, not implementation shortlist.

## What Not To Confuse With Solving This Problem

Mesh reconstruction and point cloud processing libraries are useful infrastructure, but they do not solve CAD reverse engineering by themselves:

- Open3D, PCL, Poisson reconstruction, PointSDF-style implicit reconstruction: point cloud -> mesh/implicit surface, not editable CAD.
- Scan2CAD-style alignment: scan -> matched existing CAD model pose, not reconstruction of a new CAD model.
- Text-to-CAD repositories: text/image -> CAD program, not point cloud reverse engineering unless they explicitly support point cloud input.

## Recommended Plan For Our Work

### Phase 1: Make Current Point2CAD Useful On Raw Inputs

Goal: raw point cloud -> `.xyzc` -> Point2CAD outputs.

Candidates:

1. `Hippogriff/parsenet-codebase`
2. `SimingYan/HPNet`
3. `lingxiaoli94/SPFN`

Tasks:

- run one segmentation model on sample ABC/Fusion point clouds;
- convert predicted segment labels to Point2CAD `x y z surface_id`;
- run current `point2cad.main`;
- evaluate mesh/topology quality.

### Phase 2: Test Editable CAD-Code Route

Goal: raw point cloud -> CadQuery code -> STEP.

Candidates:

1. `filaPro/cad-recode`
2. `col14m/cadrille`

Tasks:

- run provided inference demos;
- export generated CadQuery to STEP;
- compare against Point2CAD output by Chamfer, validity, and manual editability.

### Phase 3: Decide Whether B-Rep Chain Recovery Is Worth It

Candidate:

- `guohaoxiang/ComplexGen`

Use only if we need B-Rep-like topology more than simple surface fitting or CadQuery code. Integration cost is high.

### Phase 4: Build A Small Benchmark Harness

For each candidate, track:

- accepted input format;
- output format: mesh, topology JSON, CadQuery, STEP, CSG;
- install effort;
- inference time;
- failure rate;
- Chamfer distance to source cloud;
- surface segmentation quality if applicable;
- topology validity: dangling edges, self-intersections, non-manifold faces;
- editability: can a human modify hole radius, extrusion depth, fillet/chamfer?

This will keep us from mistaking a nice demo for a robust reverse-engineering pipeline.

## Current Recommendation

The best engineering path is not to replace Point2CAD immediately.

Use Point2CAD as the surface/topology branch, then add a segmentation front-end. In parallel, evaluate CAD-Recode/Cadrille as a separate CAD-program branch. If one of the CadQuery routes produces good STEP files on our target parts, it may become the main product path; if not, Point2CAD plus explicit topology/CAD export gives us a more controllable classical pipeline.
