"""Pre-built composite document factories for Tellurium simulations."""


def make_tellurium_document(
    model='',
    model_format='antimony',
    model_file='',
    integrator='cvode',
    absolute_tolerance=1e-10,
    relative_tolerance=1e-8,
    seed=-1,
    species_overrides=None,
    parameter_overrides=None,
    interval=1.0,
):
    """Create a composite document for a Tellurium simulation.

    Returns a document dict ready for use with Composite().

    Args:
        model: Antimony or SBML source string.
        model_format: 'antimony' or 'sbml'.
        model_file: Optional path to a local model file.
        integrator: 'cvode' or 'gillespie'.
        absolute_tolerance, relative_tolerance: CVODE tolerances.
        seed: Stochastic RNG seed (-1 to leave unset).
        species_overrides: {species_id: initial_value}.
        parameter_overrides: {parameter_id: value}.
        interval: Time interval between process updates.

    Returns:
        dict: Composite document with tellurium process, stores, and emitter.
    """
    species_overrides = species_overrides or {}
    parameter_overrides = parameter_overrides or {}

    return {
        'tellurium': {
            '_type': 'process',
            'address': 'local:TelluriumProcess',
            'config': {
                'model': model,
                'model_format': model_format,
                'model_file': model_file,
                'integrator': integrator,
                'absolute_tolerance': absolute_tolerance,
                'relative_tolerance': relative_tolerance,
                'seed': seed,
                'species_overrides': species_overrides,
                'parameter_overrides': parameter_overrides,
            },
            'interval': interval,
            'inputs': {},
            'outputs': {
                'species': ['stores', 'species'],
                'rates': ['stores', 'rates'],
                'parameters': ['stores', 'parameters'],
                'time': ['stores', 'time'],
            },
        },
        'stores': {},
        'emitter': {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'emit': {
                    'species': 'map[float]',
                    'rates': 'map[float]',
                    'time': 'float',
                    'global_time': 'float',
                },
            },
            'inputs': {
                'species': ['stores', 'species'],
                'rates': ['stores', 'rates'],
                'time': ['stores', 'time'],
                'global_time': ['global_time'],
            },
        },
    }
