# Curriculum Graph Visualizer

This React app uses [dagre-d3-react](https://github.com/justin-coberly/dagre-d3-react) to display curriculum graphs. Curriculum graph styles are defined in the [HKN Wiki](https://github.com/hkn-alpha/wiki), but a rough copy of the styles is copied here for easier local development.

## Specifying Edges and Nodes

Nodes are specified as an export `nodes` from `src/nodes.ts`, where

```
typeof nodes = {
    id: string;
    label: string;
    dept: string;
    num: string;
}[]
```

Edges are specified as an export `edges` from `src/edges.ts`, where

```
typeof edges = [
    string, // source node id
    string, // dest node id
    boolean // true iff corequisite relation
][]
```

The easiest way to generate these files is with `build.py` in the root folder.

## Building Graphs

The React root element is customizable to support embedding curriculum graphs into other pages not managed by React.

Run

```
REACT_APP_ROOT_ELEMENT=html_id_of_root npm run build
```

to build the graph. This will generate a file `main.<hash>.js` located in the `build/` folder. Copy this to your application, and include it in a page that has an HTML element with the ID you specified above. The graph will automatically render.

### IMPORTANT

To create a visually appealing graph, you may need to tweak some Dagre settings, particularly `rankdir` and `align`. `App.tsx` contains some comments about this, and you
can find more information at the [Dagre docs](https://github.com/dagrejs/dagre/wiki#configuring-the-layout).

ALWAYS CHECK THE GRAPH'S APPEARANCE LOCALLY FIRST!! See below for instructions.

## Debugging Locally

Run `npm start` in this folder, and open `https://localhost:3000` in your browser to see a live copy of the current graph (you'll need edges and nodes defined first).
