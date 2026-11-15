"""Two-layer grid maze router used by build_board.py.

Not a general autorouter: it routes one net at a time (Prim-style growth from the
already-connected copper to the nearest unconnected copper island) on a fine grid,
then pulls the grid path straight against exact shapely clearance checks.
Every result is re-checked by KiCad DRC afterwards; the router only has to be
conservative, not exact.

Layers: 0 = F.Cu, 1 = B.Cu.
"""
import heapq
import math
from array import array

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

HARD = 65535


class Rules:
    clearance = 0.2       # copper to copper
    hole_clearance = 0.25  # copper to drill edge
    hole_to_hole = 0.5    # drill edge to drill edge
    edge_clearance = 0.3  # copper to board edge (incl. mouse-bite holes)
    via_dia = 0.6
    via_drill = 0.3
    margin = 0.03         # grid rasterisation safety margin


class Item:
    """One piece of copper: geom per layer (dict layer->shapely), optional drill (Point, r)."""
    __slots__ = ("net", "geoms", "drill", "kind", "is_pad")

    def __init__(self, net, geoms, drill=None, kind="", is_pad=False):
        self.net = net
        self.geoms = geoms
        self.drill = drill
        self.kind = kind
        self.is_pad = is_pad


class Router:
    def __init__(self, bounds, outline, res=0.05, rules=Rules):
        self.R = rules
        self.res = res
        xmin, ymin, xmax, ymax = bounds
        self.x0, self.y0 = xmin - 1.0, ymin - 1.0
        self.nx = int(math.ceil((xmax - self.x0 + 1.0) / res)) + 1
        self.ny = int(math.ceil((ymax - self.y0 + 1.0) / res)) + 1
        shp = (self.ny, self.nx)
        self.cu = [np.zeros(shp, np.uint16), np.zeros(shp, np.uint16)]
        self.hole = np.zeros(shp, np.uint16)
        self.pads_any = np.zeros(shp, bool)
        self.keep = [np.zeros(shp, bool), np.zeros(shp, bool)]
        self.outline = outline  # shapely polygon (board, mouse bites as holes)
        self.inner = outline.buffer(-rules.edge_clearance)
        out = box(self.x0, self.y0, self.x0 + self.nx * res, self.y0 + self.ny * res).difference(self.inner)
        self.edge = np.zeros(shp, bool)
        self._fill(self.edge, out.buffer(rules.margin), True)
        self.items = []
        self.keep_geoms = [[], []]
        self.net_pref = {}

    # ---------------------------------------------------------------- raster
    def _rast(self, geom):
        if geom.is_empty:
            return None
        minx, miny, maxx, maxy = geom.bounds
        j0 = max(int(math.floor((minx - self.x0) / self.res)) - 1, 0)
        i0 = max(int(math.floor((miny - self.y0) / self.res)) - 1, 0)
        j1 = min(int(math.ceil((maxx - self.x0) / self.res)) + 2, self.nx)
        i1 = min(int(math.ceil((maxy - self.y0) / self.res)) + 2, self.ny)
        if j1 <= j0 or i1 <= i0:
            return None
        img = Image.new("1", (j1 - j0, i1 - i0), 0)
        d = ImageDraw.Draw(img)
        polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        for p in polys:
            if p.geom_type != "Polygon" or p.is_empty:
                continue

            def tr(ring):
                return [((x - self.x0) / self.res - j0, (y - self.y0) / self.res - i0) for x, y in ring.coords]

            d.polygon(tr(p.exterior), fill=1, outline=1)
            for h in p.interiors:
                d.polygon(tr(h), fill=0, outline=0)
        return i0, j0, np.array(img, dtype=bool)

    def _fill(self, arr, geom, value):
        r = self._rast(geom)
        if r is None:
            return
        i0, j0, m = r
        sub = arr[i0:i0 + m.shape[0], j0:j0 + m.shape[1]]
        sub[m] = value

    def _fill_window(self, arr, geom, i0, j0):
        r = self._rast(geom)
        if r is None:
            return
        a, b, m = r
        a -= i0
        b -= j0
        ny, nx = arr.shape
        ia0, ja0 = max(a, 0), max(b, 0)
        ia1, ja1 = min(a + m.shape[0], ny), min(b + m.shape[1], nx)
        if ia1 > ia0 and ja1 > ja0:
            arr[ia0:ia1, ja0:ja1] |= m[ia0 - a:ia1 - a, ja0 - b:ja1 - b]

    def _own(self, arr, geom, net):
        r = self._rast(geom)
        if r is None:
            return
        i0, j0, m = r
        sub = arr[i0:i0 + m.shape[0], j0:j0 + m.shape[1]]
        n = HARD if net <= 0 else net
        cur = sub[m]
        cur = np.where(cur == 0, n, np.where(cur == n, n, HARD)).astype(np.uint16)
        sub[m] = cur

    # ---------------------------------------------------------------- items
    def add_item(self, it):
        R = self.R
        self.items.append(it)
        for L, g in it.geoms.items():
            self._own(self.cu[L], g.buffer(R.clearance + R.margin, 8), it.net)
            if it.is_pad:
                self._fill(self.pads_any, g.buffer(R.clearance + R.margin, 8), True)
        if it.drill is not None:
            c, r = it.drill
            # copper of other nets must keep hole_clearance from this drill; own-net copper may touch (PTH)
            self._own(self.hole, c.buffer(r + R.hole_clearance + R.margin, 16), it.net if it.geoms else -1)

    def add_keepout(self, L, geom):
        self.keep_geoms[L].append(geom)
        self._fill(self.keep[L], geom.buffer(self.R.margin), True)

    # ---------------------------------------------------------------- connectivity
    def components(self, net):
        its = [it for it in self.items if it.net == net]
        n = len(its)
        parent = list(range(n))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for L in (0, 1):
            idx = [k for k, it in enumerate(its) if L in it.geoms]
            if not idx:
                continue
            geoms = [its[k].geoms[L].buffer(0.001) for k in idx]
            tree = STRtree(geoms)
            for a, g in enumerate(geoms):
                for b in tree.query(g, predicate="intersects"):
                    if b > a:
                        ra, rb = find(idx[a]), find(idx[b])
                        if ra != rb:
                            parent[ra] = rb
        groups = {}
        for k in range(n):
            groups.setdefault(find(k), []).append(its[k])
        return list(groups.values())

    # ---------------------------------------------------------------- exact checker
    def build_checker(self, net, hw, extra=()):
        R = self.R
        trees = []
        for L in (0, 1):
            geoms = []
            for it in self.items:
                if L in it.geoms and it.net != net:
                    geoms.append(it.geoms[L].buffer(R.clearance + 0.01, 8))
                if it.drill is not None and not (it.net == net and it.geoms):
                    c, r = it.drill
                    geoms.append(c.buffer(r + R.hole_clearance + 0.01, 16))
            geoms += [g for g in self.keep_geoms[L]]
            geoms += [g for g, LL in extra if LL is None or LL == L]
            trees.append((STRtree(geoms), geoms))
        drills = [it.drill for it in self.items if it.drill is not None]
        dtree = STRtree([c.buffer(r) for c, r in drills])
        pads = [it.geoms[L] for it in self.items if it.is_pad for L in it.geoms]
        ptree = STRtree(pads) if pads else None
        inner = self.inner

        def seg_ok(L, a, b, w=None):
            s = LineString([a, b]).buffer(hw if w is None else w / 2, 8)
            if not inner.contains(s):
                return False
            t, g = trees[L]
            return len(t.query(s, predicate="intersects")) == 0

        def via_ok(p):
            vr = R.via_dia / 2
            s = Point(p).buffer(vr, 16)
            if not inner.contains(s):
                return False
            for L in (0, 1):
                if len(trees[L][0].query(s, predicate="intersects")):
                    return False
            hs = Point(p).buffer(R.via_drill / 2 + R.hole_to_hole - 0.001, 16)
            if len(dtree.query(hs, predicate="intersects")):
                return False
            hs2 = Point(p).buffer(vr + R.hole_clearance - 0.001, 16)
            if len(dtree.query(hs2, predicate="intersects")):
                return False
            if ptree is not None and len(ptree.query(Point(p).buffer(vr + R.clearance - 0.001), predicate="intersects")):
                return False
            return True

        return seg_ok, via_ok

    # ---------------------------------------------------------------- search
    def route_connection(self, net, src_items, dst_items, hw, layer_cost=(1.0, 1.0), via_cost=1.5,
                         window_margin=6.0, allow_via=True, weight=1.15, cost_maps=(), forbid=()):
        R = self.R
        res = self.res
        allg = [g for it in src_items + dst_items for g in it.geoms.values()]
        minx, miny, maxx, maxy = unary_union(allg).bounds
        j0 = max(int((minx - window_margin - self.x0) / res), 0)
        i0 = max(int((miny - window_margin - self.y0) / res), 0)
        j1 = min(int((maxx + window_margin - self.x0) / res) + 1, self.nx)
        i1 = min(int((maxy + window_margin - self.y0) / res) + 1, self.ny)
        ny, nx = i1 - i0, j1 - j0
        sl = (slice(i0, i1), slice(j0, j1))

        hole = self.hole[sl]
        hole_blk = (hole != 0) & (hole != net)
        edge = self.edge[sl]
        free = []
        cu_blk = []
        fb_extra = [np.zeros((ny, nx), bool), np.zeros((ny, nx), bool)]
        for g, L in forbid:
            for LL in ((0, 1) if L is None else (L,)):
                self._fill_window(fb_extra[LL], g, i0, j0)
        for L in (0, 1):
            c = self.cu[L][sl]
            cb = (c != 0) & (c != net)
            cu_blk.append(cb)
            blk = cb | hole_blk | self.keep[L][sl] | edge | fb_extra[L]
            dist = ndimage.distance_transform_edt(~blk) * res
            free.append(dist > hw + 1e-9)
        if allow_via:
            vr = R.via_dia / 2
            vb = cu_blk[0] | cu_blk[1] | self.keep[0][sl] | self.keep[1][sl] | edge | self.pads_any[sl]
            dv = ndimage.distance_transform_edt(~vb) * res
            hv = ndimage.distance_transform_edt(~(hole != 0)) * res
            extra = max(R.hole_to_hole + R.via_drill / 2, R.hole_clearance + vr) - R.hole_clearance - R.margin
            via_ok = (dv > vr + 1e-9) & (hv > extra + 1e-9) & free[0] & free[1]
        else:
            via_ok = np.zeros((ny, nx), bool)

        N = nx * ny

        def mark(items_):
            m = [np.zeros((ny, nx), bool), np.zeros((ny, nx), bool)]
            for it in items_:
                for L, g in it.geoms.items():
                    r = self._rast(g)
                    if r is None:
                        continue
                    a, b, mm_ = r
                    a -= i0
                    b -= j0
                    ia0, ja0 = max(a, 0), max(b, 0)
                    ia1, ja1 = min(a + mm_.shape[0], ny), min(b + mm_.shape[1], nx)
                    if ia1 <= ia0 or ja1 <= ja0:
                        continue
                    m[L][ia0:ia1, ja0:ja1] |= mm_[ia0 - a:ia1 - a, ja0 - b:ja1 - b]
            return [m[0] & free[0], m[1] & free[1]]

        src = mark(src_items)
        dst = mark(dst_items)
        if not (src[0].any() or src[1].any()):
            return None, "no free source cells"
        if not (dst[0].any() or dst[1].any()):
            return None, "no free target cells"

        fb = [bytearray(free[0].astype(np.uint8).tobytes()), bytearray(free[1].astype(np.uint8).tobytes())]
        vb = bytearray(via_ok.astype(np.uint8).tobytes())
        tgt = bytearray((np.concatenate([dst[0].ravel(), dst[1].ravel()])).astype(np.uint8).tobytes())
        di, dj = np.nonzero(dst[0] | dst[1])
        ti0, ti1, tj0, tj1 = di.min(), di.max(), dj.min(), dj.max()
        fmin = min(layer_cost)
        g = array("d", [1e18]) * (2 * N)
        parent = array("i", [-1]) * (2 * N)
        heap = []
        for L in (0, 1):
            si, sj = np.nonzero(src[L])
            for i, j in zip(si.tolist(), sj.tolist()):
                s = L * N + i * nx + j
                g[s] = 0.0
                heap.append((0.0, s))
        heapq.heapify(heap)
        sq2 = math.sqrt(2)
        moves = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
                 (-1, -1, sq2), (-1, 1, sq2), (1, -1, sq2), (1, 1, sq2)]
        lc = layer_cost
        fac = None
        if cost_maps:
            fac = []
            for L in (0, 1):
                m = np.full((ny, nx), lc[L], float)
                for cg, LL, cf in cost_maps:
                    if LL == L:
                        mk = np.zeros((ny, nx), bool)
                        self._fill_window(mk, cg, i0, j0)
                        m[mk] *= cf
                fac.append(array("d", (m * res).ravel().tolist()))
        found = -1
        pop = heapq.heappop
        push = heapq.heappush
        closed = bytearray(2 * N)
        while heap:
            f, s = pop(heap)
            if closed[s]:
                continue
            closed[s] = 1
            if tgt[s]:
                found = s
                break
            L = 1 if s >= N else 0
            c = s - L * N
            i, j = divmod(c, nx)
            gs = g[s]
            fl = fb[L]
            step = res * lc[L]
            fcl = fac[L] if fac is not None else None
            for di_, dj_, w in moves:
                ii, jj = i + di_, j + dj_
                if ii < 0 or jj < 0 or ii >= ny or jj >= nx:
                    continue
                cc = ii * nx + jj
                if not fl[cc]:
                    continue
                if w > 1.0 and not (fl[i * nx + jj] and fl[ii * nx + j]):
                    continue
                t = L * N + cc
                ng = gs + (fcl[cc] if fcl is not None else step) * w
                if ng < g[t]:
                    g[t] = ng
                    parent[t] = s
                    dI = 0 if ti0 <= ii <= ti1 else (ti0 - ii if ii < ti0 else ii - ti1)
                    dJ = 0 if tj0 <= jj <= tj1 else (tj0 - jj if jj < tj0 else jj - tj1)
                    h = (max(dI, dJ) + (sq2 - 1) * min(dI, dJ)) * res * fmin
                    push(heap, (ng + weight * h, t))
            if vb[c]:
                t = (1 - L) * N + c
                ng = gs + via_cost
                if ng < g[t]:
                    g[t] = ng
                    parent[t] = s
                    push(heap, (ng, t))
        if found < 0:
            return None, "no path"
        path = []
        s = found
        while s >= 0:
            L = 1 if s >= N else 0
            c = s - L * N
            i, j = divmod(c, nx)
            path.append((L, self.x0 + (j + j0) * res, self.y0 + (i + i0) * res))
            s = parent[s]
        path.reverse()
        return path, "ok"

    # ---------------------------------------------------------------- path to geometry
    def path_to_segments(self, path, net, hw, forbid=()):
        """Split by layer, merge collinear steps, string-pull with exact checks."""
        seg_ok, via_ok = self.build_checker(net, hw, forbid)
        runs = []
        cur = [path[0]]
        for p in path[1:]:
            if p[0] != cur[-1][0]:
                runs.append(cur)
                cur = [p]
            else:
                cur.append(p)
        runs.append(cur)
        segs = []
        vias = []
        for k, run in enumerate(runs):
            L = run[0][0]
            pts = [(x, y) for _, x, y in run]
            # drop collinear
            red = [pts[0]]
            for a in range(1, len(pts) - 1):
                x0, y0 = red[-1]
                x1, y1 = pts[a]
                x2, y2 = pts[a + 1]
                if abs((x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)) > 1e-9:
                    red.append(pts[a])
            if len(pts) > 1:
                red.append(pts[-1])
            # string pulling
            out = [red[0]]
            i = 0
            while i < len(red) - 1:
                j = len(red) - 1
                while j > i + 1 and not seg_ok(L, red[i], red[j]):
                    j -= 1
                out.append(red[j])
                i = j
            for a, b in zip(out, out[1:]):
                if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-6:
                    segs.append((L, a, b))
            if k < len(runs) - 1:
                vias.append(pts[-1])
        return segs, vias

    def segment_item(self, net, L, a, b, w):
        return Item(net, {L: LineString([a, b]).buffer(w / 2, 8)}, kind="track")

    def via_item(self, net, p):
        g = Point(p).buffer(self.R.via_dia / 2, 16)
        return Item(net, {0: g, 1: g}, drill=(Point(p), self.R.via_drill / 2), kind="via")
