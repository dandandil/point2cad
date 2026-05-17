# Working Notes: Reverse Engineering CAD from Point Clouds

## What We Are Doing

Мы занимаемся reverse engineering CAD-модели из 3D-облака точек.
Идея проекта Point2CAD: взять скан или сэмпл CAD-объекта в виде point cloud и восстановить из него CAD-подобное представление: поверхности, ребра и углы.

Важно: текущий код в этом репозитории фокусируется не на сыром скане целиком, а на второй части пайплайна. На вход ожидается уже размеченное облако точек в формате:

```text
x y z surface_id
```

То есть каждая точка должна иметь координаты `(x, y, z)` и id поверхности `surface_id`, к которой она относится.

## Pipeline

1. Загрузить аннотированное облако точек из `.xyzc`.
2. Нормализовать координаты точек.
3. Разделить точки по `surface_id`.
4. Для каждого сегмента поверхности подобрать лучший тип поверхности:
   - plane
   - sphere
   - cylinder
   - cone
   - open spline через INR-модель
5. Сохранить "unclipped" поверхности, готовые для попарных пересечений.
6. Слить и обрезать поверхности через пересечения, чтобы получить clipped mesh.
7. Из пересечений clipped-поверхностей восстановить топологию:
   - curves / edges
   - corners

## Inputs And Outputs

Вход:

- пример: `assets/abc_00949.xyzc`
- формат: 4 числа на строку: `x y z surface_id`
- если есть только сырое облако без surface labels, перед Point2CAD нужен отдельный этап сегментации, например ParseNet или HPNet.

Выход по умолчанию пишется в `out`:

- `out/unclipped/mesh.ply` - восстановленные не обрезанные поверхности
- `out/clipped/mesh.ply` - поверхности после обрезки по пересечениям
- `out/topo/topo.json` - ребра и углы, найденные как пересечения поверхностей

## Important Code Paths

- `point2cad/main.py` - основной CLI-пайплайн.
- `point2cad/fitting_one_surface.py` - fitting одной поверхности и выбор лучшего типа поверхности.
- `point2cad/primitive_forward.py` - fitting и sampling базовых примитивов.
- `point2cad/io_utils.py` - сохранение mesh-результатов и восстановление topology.
- `visualize/visualize.py` - простой просмотр `clipped/mesh.ply` и `topo/topo.json`.

## Stable Point Cloud To B-Rep Pipeline

Стабильный путь не должен быть одной черной коробкой `point cloud -> B-Rep`.
Нужен гибрид: ML помогает с сегментацией и initial guesses, а финальная геометрия и topology собираются детерминированными CAD/geometry алгоритмами.

Рекомендуемый пайплайн:

1. Raw point cloud preprocessing:
   - убрать выбросы;
   - выровнять плотность точек;
   - оценить normals;
   - найти sharp edges и curvature jumps.
2. Surface segmentation:
   - каждая точка получает `surface_id`;
   - ML-модели типа `HPNet`, `ParSeNet`, `SPFN` используются как proposal;
   - результат надо дополнительно merge/split по residual, normals и связности.
3. Surface fitting:
   - сначала пробовать analytic primitives: plane, cylinder, cone, sphere, torus;
   - B-spline/NURBS fitting использовать только там, где primitives дают плохой residual;
   - для сплайнов нужна устойчивая UV-параметризация patch-а и least-squares fitting с regularization/fairness.
4. Topology recovery:
   - строить untrimmed fitted surfaces;
   - пересекать поверхности попарно;
   - из пересечений получать edge curves;
   - пересечения edge curves дают vertices/corners;
   - для каждой face собрать trimming loops.
5. B-Rep assembly:
   - собирать через OpenCascade/pythonOCC: `Geom_Plane`, `Geom_CylindricalSurface`, `Geom_BSplineSurface`, `Geom_BSplineCurve`;
   - создавать `TopoDS_Edge`, `TopoDS_Wire`, `TopoDS_Face`;
   - делать sewing, fixing, validation;
   - экспортировать в STEP только после проверки shell/solid.

Короткая схема:

```text
point cloud
  -> denoise / normals / resample
  -> surface segmentation
  -> primitive + spline fitting
  -> pairwise surface intersections
  -> edge/corner snapping
  -> trimming loops
  -> OpenCascade B-Rep faces
  -> sew shell/solid
  -> STEP
```

Критичные правила стабильности:

- вести единый tolerance budget: scan noise `sigma`, fitting tolerance `2-3 sigma`, snap tolerance `3-5 sigma`;
- предпочитать analytic primitives сплайнам, если residual сопоставим;
- сплайны использовать для freeform patches, а не как универсальную замену CAD-примитивам;
- валидировать каждую face: residual, normals, self-intersection, loop closure;
- сохранять промежуточные артефакты: segments, fitted surfaces, intersection curves, topology graph;
- сначала собирать корректный shell, и только потом пытаться получить solid.

Для текущего репозитория практический маршрут:

1. Добавить front-end для raw cloud -> `surface_id`.
2. Использовать Point2CAD для fitted surfaces и topology.
3. Добавить backend OpenCascade/pythonOCC для превращения surfaces + `topo.json` в B-Rep/STEP.

## Practical Framing

Наша рабочая задача: использовать или адаптировать Point2CAD как основу для восстановления CAD-геометрии из облака точек.

Смежный анализ GitHub-репозиториев и альтернативных подходов записан в [GITHUB_RESEARCH.md](GITHUB_RESEARCH.md).

Ближайшие инженерные вопросы:

- как получать или генерировать `surface_id` для наших входных облаков;
- насколько хорошо базовые примитивы и INR-spline покрывают наши реальные детали;
- нужно ли сохранять результат только как mesh/topology или экспортировать дальше в CAD-форматы;
- как валидировать качество реконструкции: ошибка fitting, корректность ребер, замкнутость/чистота topology.
