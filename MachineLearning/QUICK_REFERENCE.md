# 🚀 Quick Reference - Refactoring Patterns

**Per chi riprende il refactoring**: Questa è la tua guida rapida!

---

## 📁 File da Consultare

1. **REFACTORING_SUMMARY.md** - Overview completo, stato, cosa fare
2. **ARCHITECTURE.md** - Principi, pattern, esempi
3. **REFACTORING_PROGRESS.md** - Dettagli tecnici, decisioni
4. **application/services/parser_service.py** - REFERENCE IMPLEMENTATION

---

## 🎯 Pattern: Creare una Nuova Interfaccia

```python
# domain/interfaces/my_interface.py
from abc import ABC, abstractmethod
from typing import List

class IMyInterface(ABC):
    """Interface for..."""

    @abstractmethod
    def my_method(self, param: str) -> List[str]:
        """
        Description.

        Args:
            param: Description

        Returns:
            Description

        Example:
            >>> impl = MyImplementation()
            >>> result = impl.my_method("test")
        """
        pass
```

---

## 🎯 Pattern: Creare un Domain Model

```python
# domain/models/my_model.py
from dataclasses import dataclass
from typing import List

@dataclass
class MyModel:
    """Description"""

    # Required fields
    name: str
    value: int

    # Optional with defaults
    optional: str = ""

    def validate(self) -> List[str]:
        """Validate and return errors"""
        errors = []
        if not self.name:
            errors.append("Name is required")
        if self.value < 0:
            errors.append("Value must be >= 0")
        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0
```

---

## 🎯 Pattern: Creare un Service

```python
# application/services/my_service.py
import logging
from typing import List
from domain.interfaces.my_interface import IMyInterface
from domain.models.my_model import MyModel
from domain.exceptions import MyServiceError

logger = logging.getLogger(__name__)


class MyService:
    """
    Service for...

    Responsibilities:
    1. ...
    2. ...

    Example:
        >>> impl = MyImplementation()
        >>> service = MyService(impl)
        >>> result = service.process()
    """

    def __init__(self, dependency: IMyInterface):
        """
        Initialize service with dependencies.

        Args:
            dependency: Implementation of IMyInterface
        """
        self._dependency = dependency
        logger.info("MyService initialized")

    def process(self, data: str) -> List[MyModel]:
        """
        Main processing method.

        Args:
            data: Input data

        Returns:
            Processed results

        Raises:
            MyServiceError: If processing fails
        """
        try:
            # 1. Validate
            self._validate(data)

            # 2. Process
            result = self._dependency.my_method(data)

            # 3. Convert to models
            models = self._convert_to_models(result)

            logger.info(f"Processed {len(models)} items")
            return models

        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)
            raise MyServiceError(f"Failed to process: {e}")

    def _validate(self, data: str) -> None:
        """Validate inputs"""
        if not data:
            raise ValueError("Data cannot be empty")

    def _convert_to_models(self, items: List[str]) -> List[MyModel]:
        """Convert to domain models"""
        models = []
        for item in items:
            model = MyModel(name=item, value=len(item))
            if model.is_valid():
                models.append(model)
        return models
```

---

## 🎯 Pattern: Implementare un'Interfaccia

```python
# infrastructure/my_category/my_implementation.py
from typing import List
from domain.interfaces.my_interface import IMyInterface


class MyImplementation(IMyInterface):
    """
    Implementation of IMyInterface using...

    Example:
        >>> impl = MyImplementation()
        >>> result = impl.my_method("test")
    """

    def __init__(self, config: dict = None):
        self._config = config or {}

    def my_method(self, param: str) -> List[str]:
        """
        Implementation details...
        """
        # Your implementation here
        return [param.upper()]
```

---

## 🎯 Pattern: Migrare Codice Esistente

### Step 1: Identificare il Componente

```python
# VECCHIO: module/something/old_implementation.py
class OldImplementation:
    def do_something(self, data):
        # Existing logic
        return result
```

### Step 2: Creare/Identificare Interfaccia

```python
# domain/interfaces/something.py
class ISomething(ABC):
    @abstractmethod
    def do_something(self, data: str) -> List[str]:
        pass
```

### Step 3: Adattare Implementazione

```python
# infrastructure/something/new_implementation.py
from domain.interfaces.something import ISomething

class NewImplementation(ISomething):  # Implements interface
    def do_something(self, data: str) -> List[str]:
        # Copy existing logic from OldImplementation
        # Add type hints
        # Add validation
        # Add logging
        return result
```

### Step 4: Creare Service (se orchestrazione necessaria)

```python
# application/services/something_service.py
class SomethingService:
    def __init__(self, impl: ISomething):
        self._impl = impl

    def process(self, data):
        # Orchestration logic
        result = self._impl.do_something(data)
        return result
```

---

## 🎯 Checklist: Nuovo Componente

### Per ogni nuovo file creato:

- [ ] ✅ Docstring sulla classe/funzione
- [ ] ✅ Type hints completi
- [ ] ✅ Validation degli input
- [ ] ✅ Error handling con custom exceptions
- [ ] ✅ Logging appropriato
- [ ] ✅ Esempi nel docstring
- [ ] ✅ Metodo validate() se domain model
- [ ] ✅ Test unitario creato

---

## 🎯 Comando Rapidi

### Verificare struttura
```bash
tree domain/ application/ infrastructure/ presentation/
```

### Verificare sintassi
```bash
python -m py_compile file.py
```

### Verificare imports
```bash
python -c "from domain.interfaces.parser import IParser"
```

### Verificare type hints
```bash
python -m mypy domain/ application/
```

### Run tests
```bash
python -m pytest tests/ -v
```

---

## 🎯 Priorità del Lavoro

### Alta Priorità (Fare prima):
1. Completare Services rimanenti (Storage, DataCollection, Training)
2. Migrare parser esistente
3. Creare StorageFactory
4. Implementare retry logic

### Media Priorità:
5. Migrare resto codice
6. Rimuovere duplicati
7. Pydantic settings

### Bassa Priorità:
8. Tests completi
9. Performance optimization
10. Cleanup finale

---

## 🎯 Errori Comuni da Evitare

### ❌ NON Fare:

1. **Importare infrastructure in domain**
   ```python
   # domain/models/sample.py
   from infrastructure.parser import TreeSitter  # ❌ WRONG!
   ```

2. **Implementare logica in interfaccia**
   ```python
   class IParser(ABC):
       def parse(self, code):
           return []  # ❌ WRONG! Abstract only!
   ```

3. **Dipendenze concrete in services**
   ```python
   class MyService:
       def __init__(self):
           self.parser = TreeSitterParser()  # ❌ WRONG! Use interface!
   ```

4. **Dimenticare validation**
   ```python
   def process(self, data):
       result = do_stuff(data)  # ❌ WRONG! Validate first!
   ```

### ✅ Fare:

1. **Usare interfacce**
   ```python
   def __init__(self, parser: IParser):  # ✅ CORRECT!
       self._parser = parser
   ```

2. **Validate input sempre**
   ```python
   def process(self, data: str):
       Validator.validate_not_empty(data)  # ✅ CORRECT!
       ...
   ```

3. **Log appropriato**
   ```python
   logger.info(f"Processing {len(items)} items")  # ✅ CORRECT!
   ```

4. **Handle errors specifici**
   ```python
   except FileNotFoundError as e:  # ✅ CORRECT!
       logger.error(f"File not found: {e}")
   ```

---

## 🎯 Template Rapido

### Nuovo Service Template:

```python
"""My Service"""
import logging
from typing import List
from domain.interfaces.my_interface import IMyInterface
from domain.models.my_model import MyModel

logger = logging.getLogger(__name__)


class MyService:
    """Service for..."""

    def __init__(self, dependency: IMyInterface):
        self._dependency = dependency
        logger.info("MyService initialized")

    def main_method(self, param: str) -> List[MyModel]:
        """Main method"""
        # 1. Validate
        self._validate(param)

        # 2. Process
        result = self._process(param)

        # 3. Return
        logger.info(f"Processed {len(result)} items")
        return result

    def _validate(self, param: str) -> None:
        """Validate inputs"""
        if not param:
            raise ValueError("Param cannot be empty")

    def _process(self, param: str) -> List[MyModel]:
        """Process logic"""
        return []
```

---

## 💡 Tips

1. **Studia ParserService** - È il template perfetto
2. **Copia i pattern** - Non reinventare la ruota
3. **Test incrementale** - Testa dopo ogni modifica
4. **Commit frequenti** - Piccoli commit atomici
5. **Consulta ARCHITECTURE.md** - Per dubbi sui principi

---

## 🔗 Link Utili

- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architettura completa
- [REFACTORING_PROGRESS.md](REFACTORING_PROGRESS.md) - Dettagli tecnici
- [application/services/parser_service.py](application/services/parser_service.py) - Reference

---

**Buon Refactoring! 🚀**
