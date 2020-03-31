# Summary of available options:
- **--runcore** run only core tests (methods annotated with @pytest.mark.core)
- **-m unit** (run tests originated from classes marked for unit testing (annotated with @pytest.mark.unit)
- **-m integration** (run tests originated from classes marked for integration testing (annotated with @pytest.mark.unit)
- **-rs**  display short test summary info

# Usage examples:
Run core tests from unit test classes
```sh
python -m pytest --runcore -m unit ./tests/nxcals_backport
```
    
Run all integration tests
```sh
python -m pytest -m integration ./tests/nxcals_backport
```

Run all tests

```sh
python -m pytest ./tests/nxcals_backport
```