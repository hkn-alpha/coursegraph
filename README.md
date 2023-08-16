# HKN Coursegraph

This repository contains code used to build interactive course graphs for the [HKN Wiki](https://wiki.hkn.illinois.edu). If you're looking for a nice way to parse UIUC Course Explorer data, you might also find some of this code to be useful.

## Course Explorer Parsing

Course Explorer Parsing lives in `utils.py`, implemented as the `Course` and `PartialCourse` classes - a `Course` has prerequisite information (extracted from Course Explorer), and a `PartialCourse` does not. To fetch a course and its prerequisites from Course Explorer, you could run

```
from utils import PartialCourse, Course
print(Course.of_partial(PartialCourse("CS", 225)))
```

We've tried to handle all the different ways prerequisites are written (in English) in Course Explorer, but if you notice a course whose prerequisites aren't parsed properly, please let us know.

## Graph Building

`build.py` is responsible for turning a list of (core) courses into a DAG based on prerequisites. It outputs two typescript files conforming to the edges and nodes formats specified in the `visualizer` folder. To generate these, run

```
python build.py <path to course list> <path to nodes output> <path to edges output>
```

The course list may contain annotations (i.e. "(1 of 6)") on courses. Each line of the course list file should be a course name (i.e "CS225" with no spaces), followed either by a newline or a space and then an annotation (which is then followed by a newline). Examples may be found in `{cs,ee,ce}_core.txt` files.

## HKN Devloop

To update a curriculum graph:

1. Update the input file corresponding to your graph.
2. Run `python build.py <path to course list> visualizer/src/nodes.ts visualizer/src/edges.ts`
3. In `visualizer` folder, run `REACT_APP_ROOT_ELEMENT={ce,cs,ee}graph npm run build`
4. Copy `main.<hash>.js` from `visualizer/build` to `wiki/docs/static/{ce,cs,ee}_graph.js`
5. Done! Commit any changes to both repositories and open pull requests.
