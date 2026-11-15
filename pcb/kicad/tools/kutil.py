"""Small helpers around the KiCad 10 pcbnew Python API (Python 3.14 build).

SWIG iterators are broken in this build (`'SwigPyIterator' object has no attribute 'next'`),
so containers are walked by index.
"""
import math

import pcbnew

MM = 1e6


def items(container):
    return [container[i] for i in range(len(container))]


def tracks(board):
    return [t.Cast() for t in items(board.Tracks())]


def drawings(board):
    return [d.Cast() for d in items(board.Drawings())]


def zones(board):
    return [board.GetArea(i) for i in range(board.GetAreaCount())]


def mm(v):
    return v / MM


def pt(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))


def fp_transform(fp):
    """Return f(x, y) mapping footprint-local mm (orientation 0, front view) to board mm."""
    p = fp.GetPosition()
    ox, oy = mm(p.x), mm(p.y)
    th = math.radians(fp.GetOrientationDegrees())
    c, s = math.cos(th), math.sin(th)

    def f(x, y):
        return (ox + x * c + y * s, oy - x * s + y * c)

    return f


def pad_polys(pad, layer):
    """Copper outline of a pad on one layer as a list of (x, y) mm rings."""
    ps = pad.GetEffectivePolygon(layer)
    rings = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        rings.append([(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())])
    return rings


def board_outline(board):
    ps = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(ps, False)
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        ext = [(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())]
        holes = []
        for h in range(ps.HoleCount(i)):
            hh = ps.Hole(i, h)
            holes.append([(mm(hh.CPoint(k).x), mm(hh.CPoint(k).y)) for k in range(hh.PointCount())])
        out.append((ext, holes))
    return out


def add_track(board, net, layer, a, b, width):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(*a))
    t.SetEnd(pt(*b))
    t.SetWidth(int(round(width * MM)))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    return t


def add_via(board, net, p, dia=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(*p))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(int(round(dia * MM)))
    v.SetDrill(int(round(drill * MM)))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    board.Add(v)
    return v
