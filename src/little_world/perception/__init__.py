"""Seeing the field: depth cameras and finding known parts in their pictures (ADR 0032).

`sensors` holds the depth cameras, their numbers from their makers' documents (standard
library). `boxes` turns a depth picture into points and finds a known box on the surface it
stands on - remove the support plane, gather what stands on it, fit the box (numpy).
`eye` takes a picture through the MuJoCo adapter's rays and asks `boxes` where the part is.
Nothing here reads the simulator's poses of the parts it looks for.
"""
