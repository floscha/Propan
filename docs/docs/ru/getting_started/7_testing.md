---
first: Для того, чтобы протестировать его без запуска
second: необходимо модифицировать брокера с помощью
---

# Тестирование

Для того, чтобы протестировать ваше приложение локально, либо в рамках CI пайплайна, вам хочется уменьшить количество внешних зависимостей.
Гораздо проще сразу запустить набор тестов, чем пытаться поднимать контейнер с вашим Брокером Сообщений в рамках CI пайплайна.

Также, отстуствие внешних зависимостей позволит избежать ложного падения тестов, которое может быть связано с ошибками передачи данных до брокера, либо слишком ранним обращением к нему (когда контейнер еще не готов принимать сообщения).

## Модификация брокера

С этой целью **Propan** позволяет модифицировать поведение вашего брокера так, чтобы он передавал сообщения "в памяти", не требуя запуска внешних зависимостей.

Допустим, у нас есть приложение со следующим содержанием:

{% import 'getting_started/test/1.md' as includes with context %}
{{ includes }}

А затем мы делает *RPC* запрос для того, чтобы проверить результат выполнения:

{! includes/getting_started/test/2.md !}

!!! note
    При использовании тестового брокера **RPC** запросы работают даже у брокеров, которые не поддерживают их в обычном режиме.

## Использование фикстур

В больших приложений для переиспользования тестового брокера вы можете использовать фикстуру следующего содержания:

{! includes/getting_started/test/3.md !}

!!! tip
    Данный подход имеет существенный недостаток: ошибки, возникшие внутри обработчика, **не могут быть захвачены** внутри ваших тестов.

Например, следующий тест вернет `None`, а внутри обработчика - возникнет `pydantic.ValidationError`:

```python hl_lines="4 6"
{!> docs_src/quickstart/testing/4_suppressed_exc.py !}
```

Также этот тест будет заблокировать на `callback_timeout` (по умолчанию **30** секунд), что может может сильно раздражать, когда внутри разрабатываемого
обработчика возникают ошибки, а ваши тесты отваливаются по длительному таймауту с `None`.

## Прямой вызов функций

**Propan** предоставляет возможность вызывать функции-обработчики напрямую: так, как если бы это были обычные функции.

Для этого вам нужно сконструироваться сообщение с помощью метода `build_message` так, если бы это был `publish` (сигнатуры методов совпадают), а затем
передать это сообщение в ваш обработчик в качестве единственного аргумента функции.

{! includes/getting_started/test/4.md !}

При этом, если вы хотите, чтобы захватывать исключения обработчика, вам нужно использовать флаг `reraise_exc=True` при вызове:

{! includes/getting_started/test/5.md !}

Таким образом, **Propan** предоставляет вам полный инструментарий для тестирования ваших обработчиков: от валидации *RPC* ответов до корректно выполнения тела функций.
