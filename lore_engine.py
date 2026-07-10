# -*- coding: utf-8 -*-
"""
PatternGuard Desktop - Weave Lore Engine
Contains rich, keyword-triggered character chat responses for:
1. Apo Magdalena (Master Weaver of Pinili, speaking on oral traditions and symbolic geometry)
2. Dr. Julian Villon (Ethnomathematician, speaking on digital signal processing and crystallographic groups)
"""


def get_lore_response(message: str, character: str = "weaver") -> str:
    """
    Analyzes the user's chat message and returns a thematic, highly educational,
    and character-specific reply based on custom keywords.
    """
    clean_msg = message.lower().strip()

    if character == "weaver":
        # ==========================================
        # APO MAGDALENA (WEAVER RESPONSE TREE)
        # ==========================================
        if any(kw in clean_msg for kw in ["kusikus", "whirlpool", "dazzle", "spirit", "binakol"]):
            return (
                "Ay, my child! Wen, the *Kusikus* is very sacred to our people. In our village in Pinili, "
                "we warp alternating groups of indigo and white cotton threads. When you look closely, your "
                "eyes begin to spin like a whirlpool in the great Abra river! The bad wind spirits, the *mangmangkik*, "
                "they have eyes that can only see straight lines. When they approach your bed and see this Kusikus, "
                "they get so dizzy they fall into the swirl and get trapped! It is the geometric armor of our ancestors."
            )

        elif any(kw in clean_msg for kw in ["pinilian", "star", "flower", "frog", "supplementary"]):
            return (
                "Ah, the *Pinilian*! That means 'to select' or 'to choose' in our language, my child. Unlike the binakol "
                "which is woven simply with alternating check coordinates, for Pinilian, we use thin bamboo sticks to count "
                "each warp thread and pull them up by hand! We create floats that stand out like stars in the night sky "
                "(*sinan-kabalyo*) or small frogs (*sinan-tokak*) singing for rain. It requires endless patience—each thread "
                "is pulled with a quiet prayer for protection."
            )

        elif any(kw in clean_msg for kw in ["math", "symmetry", "group", "crystallograph", "equation"]):
            return (
                "Hehe, my child, those are very long and fancy words! Scholars with their computers come to my workshop "
                "and say, 'Apo, your wooden loom is solving equations!' I do not know of equations or coordinates, but "
                "I know the weight of the hand-crafted shuttle and the exact rhythm of the loom pedal. The geometry is in "
                "our blood—passed down from mother to daughter. It is the symmetry of a clean heart and a steady hand!"
            )

        elif any(kw in clean_msg for kw in ["fft", "fourier", "autocorrelation", "dsp", "signal"]):
            return (
                "My child, you speak of 'Fourier' and 'DSP' as if they are ancient spells! When we hear the shuttle beat "
                "against the wood—*tlack-tlack, tlack-tlack*—that is our signal. The rhythm of the threads is like waves of "
                "music. When you align your pitch and rotation sliders on the screen, you are just tuning your ears "
                "to the song of the old wood loom! Keep sliding them until the song is pure."
            )

        elif any(kw in clean_msg for kw in ["hello", "hi", "greet", "naimbag", "day"]):
            return (
                "Naimbag a bigatmo, my dear child! (Warmest greetings!) I am Apo Magdalena, master weaver of Pinili. "
                "The wood of my loom is polished by fifty years of work. Tell me, are you here to learn the old stories, "
                "or are you trying to calibrate our protective geometric grids today?"
            )

        else:
            return (
                "Wen, my child. Woven cloth is a voice. It tells of the wind, the mountains of Cordillera, and the ancient stars. "
                "When we weave, we keep our ancestors alive in the modern world. Ask me about the whirlpool protection of Binakol, "
                "or how we count threads for the Pinilian stars, and I will gladly share my weaving fire with you."
            )

    else:
        # ==========================================
        # DR. JULIAN VILLON (ETHNOMATHEMATICIAN)
        # ==========================================
        if any(kw in clean_msg for kw in ["kusikus", "binakol", "p4", "spirit", "vortex"]):
            return (
                "Incredible structural architecture, isn't it? The *Binakol* and *Kusikus* designs conform perfectly "
                "to the **p4 wallpaper symmetry group**. Under International Crystallographic notation, p4 possesses "
                "four-fold rotational axes (90-degree rotocenters) but completely lacks reflection planes or glide reflections! "
                "It is a chiral lattice. The dizzying 'dazzle' effect is not mere superstition; it is a physical, high-contrast "
                "grid designed to overload the human visual processing neurons—essentially a spatial frequency hack that "
                "disorients perception. No wonder legends say it traps wind spirits!"
            )

        elif any(kw in clean_msg for kw in ["pinilian", "pm", "star", "flower", "supplementary"]):
            return (
                "Ah! The *Pinilian* textiles are usually prime examples of the **pm symmetry class** (reflective parallel columns) "
                "or even complex **p4m grids** if they incorporate checkered boundaries. What makes Pinilian fascinating from "
                "a signal analysis standpoint is the use of 'floating warps'—a supplementary warp technique. Mathematically, "
                "this acts as a localized spatial amplitude modulation, injecting discrete high-frequency impulses (the stars) "
                "into a stable, repeating sinusoidal background wave!"
            )

        elif any(kw in clean_msg for kw in ["fft", "fourier", "frequency", "spectral", "spectrogram"]):
            return (
                "Exactly! When we apply a 2D Fast Fourier Transform (FFT) to a digitized weave, we decompose the spatial pattern "
                "into its fundamental spatial frequency components (u, v). In a perfectly calibrated system, you will see sharp "
                "delta Dirac peaks in the power spectrum, corresponding to the warp/weft grid spacing. If the sliders are misaligned, "
                "the spectrum spreads out, which we measure as high spectral entropy ($H_{spec}$). Calibrating the sliders "
                "essentially tunes a spatial bandpass filter to lock on to the weave's true frequency!"
            )

        elif any(kw in clean_msg for kw in ["autocorrelation", "affine", "matrix", "correlation", "rmse"]):
            return (
                "Excellent technical focus! We compute the 2D cross-autocorrelation surface ($R_{xx}$) to measure spatial "
                "translation offsets and calculate the exact 3x3 affine warping matrix:\n"
                "  M = [[a, b, tx], [c, d, ty], [0, 0, 1]]\n"
                "Comparing this to the specimen's ideal target matrix yields the Root Mean Square Error (RMSE). Once this error "
                "drops close to zero, we achieve perfect crystallographic resonance—represented as a maximum peak on the spatial "
                "autocorrelation surface!"
            )

        elif any(kw in clean_msg for kw in ["hello", "hi", "greet"]):
            return (
                "Greetings! I am Dr. Julian Villon, Ethnomathematician. I analyze indigenous textiles through the rigorous lens "
                "of 2D digital signal processing, spatial frequency grids, and wallpaper crystallography groups. How can I assist "
                "you in verifying your affine transformations or calculating spatial auto-correlation curves today?"
            )

        else:
            return (
                "A profound area of inquiry! Handloom textiles are literally mathematical matrices made physical. By counting threads, "
                "indigenous weavers executed discrete binary patterns centuries before modern computers. Feel free to ask me about "
                "the 2D Fourier transforms of these weaves, the affine transformation matrix equations, or why the p4 and pmg "
                "wallpaper groups are so geometrically distinct!"
            )