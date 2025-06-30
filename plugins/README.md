# Airflow Plugins

This directory contains custom Airflow plugins for the quant platform.

## Usage

Place custom plugins in this directory. They will be automatically loaded by Airflow.

## Plugin Types

- **Operators**: Custom task operators
- **Hooks**: External system connections
- **Sensors**: Data availability detection
- **Macros**: Template functions

## Example Structure

```
plugins/
├── operators/
│   └── custom_operator.py
├── hooks/
│   └── custom_hook.py
└── sensors/
    └── custom_sensor.py
```