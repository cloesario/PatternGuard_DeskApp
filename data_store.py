# -*- coding: utf-8 -*-
"""
PatternGuard Desktop - Specimens Dataset
Contains crystallographic metadata, regions, and target alignment coordinates for traditional
weaving patterns of the Philippines.
"""

SPECIMENS = [
    {
        "id": "concha-concha",
        "name": "Concha Concha",
        "region": "Vigan, Ilocos Sur",
        "group": "p4m",
        "groupName": "Checkerboard Mirror Grid (p4m)",
        "description": "A mathematical marvel featuring concentric checkered squares that mimic the organic, nested spirals of shells.",
        "longDescription": "Woven meticulously by master weavers in Vigan, the Concha Concha features square-within-square nested structures resembling concentric shells. Its high-contrast checkered sections reflect perfectly along both diagonal and perpendicular axes, establishing a rich p4m wallpaper symmetry.",
        "symmetricAxes": "4 reflection axes (vertical, horizontal, and both diagonals) with 4-fold rotocenter nodes.",
        "crystallographicDefinition": "The highest square symmetry system. Features 90° rotation centers at the square centers, 180° rotation points at intersections, and mirror reflection planes bounding each grid sector.",
        "targetPitch": 30.0,
        "targetRotation": 0.0,
        "targetOffsetX": 0.0,
        "targetOffsetY": 0.0,
        "targetDecay": 0.0,
        "renderType": "binakol"
    },
    {
        "id": "kinkinelleng",
        "name": "Kinkinelleng",
        "region": "Sarrat, Ilocos Norte",
        "group": "pmg",
        "groupName": "Zigzag Glide Mirror Grid (pmg)",
        "description": "A kinetic stepped checkered design arranged in vertical zigzag formations resembling high-frequency steps or ringing bells.",
        "longDescription": "The Kinkinelleng pattern gets its name from the local word for ringing bells. Woven in Sarrat, the structure displays zig-zag columns of stepped grids that slide and mirror down a central axis, embodying glide reflections. It is highly protective, symbolizing the vibrant chime of brass bells.",
        "symmetricAxes": "Parallel glide reflection vectors combined with offset 2-fold rotocenter points.",
        "crystallographicDefinition": "Contains 180° rotations, reflection lines in one coordinate direction, and glide reflection vectors perpendicular to the reflections.",
        "targetPitch": 34.0,
        "targetRotation": -15.0,
        "targetOffsetX": 8.0,
        "targetOffsetY": -6.0,
        "targetDecay": 10.0,
        "renderType": "pinilian"
    },
    {
        "id": "kulalabang",
        "name": "Kulalabang",
        "region": "Vigan, Ilocos Sur",
        "group": "p4",
        "groupName": "Four-fold Gyrational Vortex (p4)",
        "description": "Features dizzying, multi-centric square spirals that resemble complex web works or highly intricate geometric vortexes.",
        "longDescription": "The Kulalabang pattern features square-like concentric spirals that create an optical illusion of rotational movement. Traditionally representing water ripples or whirlpools, its purpose is to create a 'dazzle' effect that disorients malicious spirits.",
        "symmetricAxes": "4-fold rotational centers at the spiral vortex cores. Completely lacks reflection lines.",
        "crystallographicDefinition": "A square system where every intersection behaves as a 90-degree rotational order node, but there are no mirror planes, rendering the lattice chiral.",
        "targetPitch": 40.0,
        "targetRotation": 20.0,
        "targetOffsetX": -4.0,
        "targetOffsetY": 6.0,
        "targetDecay": 0.0,
        "renderType": "binakol"
    },
    {
        "id": "sinan-siko",
        "name": "Sinan-Siko",
        "region": "Abra, Cordillera",
        "group": "pm",
        "groupName": "Reflective Parallel Columns (pm)",
        "description": "Angled, elbow-like configurations symbolizing joint flexibility, strength, and protection, woven in alternating colored columns.",
        "longDescription": "Sinan-siko (meaning 'elbow-like') features strong chevron diagonals representing physical joints and bone structures. Historically worn by tribal warriors, its geometry mirrors across vertical channels, creating an incredibly balanced protective shield.",
        "symmetricAxes": "Parallel vertical reflection lines with translation along the columns. No rotations.",
        "crystallographicDefinition": "A rectangular grid system featuring reflection planes in a single coordinate direction, repeated translational patterns in two dimensions.",
        "targetPitch": 46.0,
        "targetRotation": -45.0,
        "targetOffsetX": 12.0,
        "targetOffsetY": -12.0,
        "targetDecay": 15.0,
        "renderType": "pinilian"
    },
    {
        "id": "kusikus",
        "name": "Kusikus",
        "region": "Pinili, Ilocos Norte",
        "group": "p4",
        "groupName": "Four-fold Gyrational Vortex (p4)",
        "description": "Swirling, circular optical illusions representing whirlpools, meant to confuse and ward off malevolent winds (the dazzle effect).",
        "longDescription": "The Kusikus is a prized ancestral binakol pattern. By alternating dark and light threads in repeating concentric blocks, the weaver creates a swirling illusion of circular whirlpools. Malicious wind spirits are believed to get trapped in this geometric labyrinth.",
        "symmetricAxes": "Four 90° rotocenters at vortex cores, completely lacking mirror reflections.",
        "crystallographicDefinition": "Translational repetitions of a 4-fold rotation matrix. Its asymmetrical chiral components render it non-mirrorable.",
        "targetPitch": 28.0,
        "targetRotation": 12.0,
        "targetOffsetX": -2.0,
        "targetOffsetY": 4.0,
        "targetDecay": 5.0,
        "renderType": "binakol"
    }
]