# Type annotations
## PEP 484

```python
def f(x):
    # type: (int) -> str
    return "x"

a = b  # type: List[int]  
```
Works but all types should be imported

## Sphinx style

```python
def f(x):
    """
    :param int x:
    """
    return None
```
Works but only single word types

```python
def f(x):
    """
    :type x: typing.List[int]
    """
    return None
```
Works and `foo.bar.baz` modules are imported.
