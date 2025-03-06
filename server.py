{
    "version": "2.5.2",
    "modules": [
        {
            "plugin": "Fundamental",
            "model": "VCO",
            "id": 0
        },
        {
            "plugin": "Fundamental",
            "model": "VCF",
            "id": 1
        },
        {
            "plugin": "Fundamental",
            "model": "Mixer",
            "id": 2
        },
        {
            "plugin": "Core",
            "model": "AudioInterface",
            "id": 3
        }
    ],
    "wires": [
        {
            "outputModuleId": 0,
            "outputId": "sin",
            "inputModuleId": 1,
            "inputId": "in"
        },
        {
            "outputModuleId": 1,
            "outputId": "lowpass",
            "inputModuleId": 2,
            "inputId": "in"
        },
        {
            "outputModuleId": 2,
            "outputId": "mix",
            "inputModuleId": 3,
            "inputId": "1"
        },
        {
            "outputModuleId": 2,
            "outputId": "mix",
            "inputModuleId": 3,
            "inputId": "2"
        }
    ]
}