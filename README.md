# ScaleChanger

ScaleChanger is a Python application designed to facilitate the scaling of data. It provides a simple interface for users to change the scale of their input data, making it easier to work with datasets of varying ranges.

## Installation

To install the required dependencies, run the following command:

```
pip install -r requirements.txt
```

## Usage

To use the ScaleChanger application, you can import the `ScaleChanger` class from the `scale_changer` package and create an instance of it. Here is a basic example:

```python
from scale_changer.main import ScaleChanger

scaler = ScaleChanger()
scaled_data = scaler.change_scale(data, new_scale)
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.