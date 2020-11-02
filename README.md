# IPtvDream 4X
[![](https://img.shields.io/bitbucket/pipelines/iptvdream/iptvdream-4x.svg)](https://bitbucket.org/iptvdream/iptvdream-4x/addon/pipelines/home)
[![CircleCI](https://circleci.com/bb/iptvdream/iptvdream-4x.svg?style=svg)](https://circleci.com/bb/iptvdream/iptvdream-4x)

Плагин для просмотра iptv на ресивeрах (тв-приставках) с enigma2.
*NO WARRANTIES[*](#markdown-header-no-warranties) (Отказ от ответственности)[*](#markdown-header-no-warranties)*.

[![](https://c5.patreon.com/external/logo/become_a_patron_button.png)](https://www.patreon.com/iptvdream4x)

Отчёты об ошибках, пожелания, предложения, пулл-реквесты и прочая помощь приветствуется!

# Release notes

## 4.98

- исправления архива антифриз
- исправления скина

## 4.97

- исправлен индикатора архива для шара-тв
- косметические изменения скина
- в списке епг открытие детального описания так же по кнопке инфо
- исправлен ipstream

## 4.96

- добавлена Шара

## 4.95

- добавлен Шурик

## 4.94

- исправлена индикация архива в плейлистах Совени
- удалён оттклуб, т.к. плейлист больше не поддерживается Совени

## 4.93

- Добавлен пользовательский плейлист для едем.
  ЕдемСовени это список каналов от Совени.
  ЕдемТВ это список каналов как в плейлисте который кладётся в бокс.
- Исправлен ввод цифр для логина и пароля.
- Косметичесие изменения крупного скина.
- Другие исправления

## 4.92

- косметические исправления скина

## 4.91

- исправлен креш если пользователь ввел недействительную ссылку плейлиста или епг

## 4.90

- исправлена ошибка с епг возникшая в предыдущей версии

## 4.89

- оптимизирован запрос епг

## 4.88

- исправлен крэш при входе в список каналов

## 4.87

- ещё раз исправлен крэш на последних DMM прошивках

## 4.86

- исправлен крэш на последних DMM прошивках

## 4.85

- исправлена проблема связанная с изменением неправильного логина
- обновлён перевод

## 4.84

- добавлена опция для выбора стартового режима плагина: все группы / избранные каналы
- исправлены ошибки в веб интерфейсе настроек

## 4.83

- добавлен веб интерфейс для редактирования настроек (beta)
- все настройки объединены в одно меню
- смена логина и пароля производится из настроек по жёлтой кнопке "Logout"

## 4.82

- исправлен крэш

## 4.81

- сделана остановка плеера при выключении
- обновлено епг для цбиллинг

## 4.80

- исправлены архивы cbilling
- исправлены архивы antifriz

## 4.79

- добавлен antifriz.tv

## 4.78

- добавлен antifriz.tv
- добавлен более контрастный FHD скин
- откат ссылок на http из-за того что DMM не поддерживает https

## 4.77

- добавлен shara.club
- добавлен более контрастный HD скин (активируется в списке провайдеров по синей кнопке)

## 4.76

- добавлен ipstream.one
- исправлен запуск некоторых провайдеров из главного меню

## 4.75

- добавлена опция использования прокси из hls в ts
- исправлена перемотка цифровыми кнопками

## 4.74

- ещё раз исправлен крэш на последней опен-атв прошивке

## 4.73

- исправлен крэш на последней опен-атв прошивке

## 4.72

- Добавлен выбор формата потока для гланца (hls или ts). По умолчанию ts, на котором плеер енигмы не зависает.

## 4.71

- добавлен glanzTV
- обновлен украинский перевод

## 4.70

- исправлена работа FullHD скина на некоторых прошивках

## 4.69

- добавлен FullHD скин (ещё будет доделываться)
- обновлен русский перевод
- добавлена возможность отображать провайдеров в списке дополнений
- добавлен перевод на литовский язык

## 4.68

- исправлен итв-лайв

## 4.67

- исправлен отсутствующий епг в списке каналов итв-лайв
- для провайдеров которым не нужен только ключ это поле отображается в настройках

## 4.66

- исправлена работа епг для вип пакета itv.live

## 4.65

- исправлен возможный крэш на картина-тв

## 4.64

- вывод названия канала на дисплее приставки
- поддержка нескольких пользовательских м3у плейлистов
- cbilling-tv теперь так же доступен в основном плагине
- добавлен itv.live
- перемотка (прыжки) в архиве с помощью кнопок 1-9 
- исправлено лого и id каналов для топ-иптв
- косметические исправления скина

## 4.63

- исправлен крэш на прошивках PKT и других в которых не соблюдается обратная совместимость
- исправлено отображение прогресс-бара при паузе в архиве

## 4.62

- добавлено top-iptv

## 4.61

- исправлен крэш при пустом списке избранное
- добавлена возможность пользовательских скинов

## 4.60

- исправлен парсер м3у в случае комментариев в плейлисте

## 4.59

- исправлен возможный крэш при отсутствии епг
- добавлена поддержка скина BlueMetalFHD

## 4.58

- Добавлена локализация плагина на украинском языке

## 4.57

- Добавлена поддержка tvg-rec тэга в для m3u плейлистов
- Шура-тв теперь использует прямую ссылку на плейлист. Для запуска в поле "логин" надо прописать свой токен.

## 4.56

- исправлен фокс-тв

## 4.55

- переход на новый домен для источника епг
- добавлен фокс-тв
- небольшое исправления парсера м3у плейлистов

## 4.54

- войти в настройки провайдера теперь можно по жёлтой кнопке в менеджере
- для м3у-плейлиста добавлена опция чтобы скачивать плейлист по ссылке
- некоторые улучшения чтения м3у плейлистов

## 4.53

- добавлена корона тв

## 4.52

- исправлена ошибка в скине на некоторых прошивках

## 4.51

- исправление для PKT прошивок
- незначительно улучшение интерфейса epg и архива

## 4.50

- добавлен 1ott, спасибо Алексу (ott-play.com) за ЕПГ
- добавлен выбор формата архива flusonic для плейлиста


## 4.49

- возможность прописать ссылку на телегид в m3u плейлисте
- возможность указать наличие архива для m3u плейлиста

## 4.48

- поддержка utf8-bom формата плейлиста
- исправлен крэш на некоторых прошивках

## 4.47

- добавлена возможность просмотра пользовательского плейлиста
- выбор сервера и другие настройки для картины
- выбор плейлиста для iptv-e2

## 4.46

- поддержка логотипов каналов для совок
- поддержка логотипов каналов для картины

## 4.45

- исправлены мелкие ошибке в скине

## 4.44

- исправлен крэш на дмм
- исправлен крэш на некоторых провайдерах

## 4.43

- добавлены логотипы каналов в инфобарe
- небольшие улучшения скина

## 4.42

- исправление крэша на атв прошивке

## 4.41

- добавлено онли4тв, спасибо @soveni

## 4.40

- немецкая локализация
- сохранение фаворитов для совок

## 4.39

- добавлены пункты в меню для открытия настроек и для очистки логина + пароля

## 4.38

- исправлен крэш при неверно выставленной дате

## 4.37

- исправлен крэш на некоторых прошивках

## 4.36

- добавлен выбор аудио дорожки
- обновлён перевод

## 4.35

- исправлен крэш при выборе keymap

## 4.34

- для эдем используется лайт плейлист, можно выбрать полный по кнопке меню находясь в списке каналов

## 4.33

- убрана пауза при вводе численного кода
- поддержка настроек на стороне апи: выбор сервера, выбор качества

## 4.32

- исправлен крэш при первом старте плагина

## 4.31

- исправлена обработка исключений в епг кеше
- id каналов m3u определяются из урл (более стабильный список избранное)
- список провайдеров отсортирован по имени
- убран эдем-yahan, используйте эдем-soveni

## 4.30

- исправлен крэш

## 4.29

- Старые хорошие фичи снова на месте:
    - Упорядочивание избранного
    - Выбор сортировки списка каналов
- Установка зависимостей при старте: json, html, exteplayer3, ServiceApp
- Добавлено новое-тв 

## 4.28

- упрощена навигация по архиву

## 4.27

- откат изменений

## 4.26

- каналы с одинаковым tvg-id для иптв-е2 и шура
- авто обновление тв - программы в списке каналов (нужно тестирование)

## 4.25

- исправлен оттклуб

## 4.24

- исправлено епг на каналах с одинаковым tvg-id
- отдельное окно для детального епг
- обновление прогрессбара в окне "епг по дням"

## 4.23

- исправлен кингмод

## 4.22

- Добавлен кинобум
- Добавлен кингмод
- Поддержка буквенных tvg-id в xmltv

## 4.21

- Добавлена картина тв
- Исправлен крэш в настройках
- Начальная реализация обновления прогресса в списке епг

## 4.20

- Исправлено сохранение favourites

## 4.19

- Добавлено pure

## 4.18

- Добавлен Эмигрант тв
- Добавлено Амиго тв
- Добавлено iptv-e2 от Совени

## 4.17

- исправлена нумерация каналов совок.тв
- отображение даты окончания подписки для наше.тв и др.

## 4.16

- исправлено имя плагина в сообщениях об ошибке
- изменён урл епг

## 4.15

- добавлена Шура
- исправлено листание групп кнопками Букет+/Букет-

## 4.14

- добавлены не достающие логотипы
- изменён урл обновления

## 4.13

- исправлены потерянные файлы

## 4.12

- добавлено лого балтик, спасибо Tall
- добавлен едем с источником епг от совени
- добавлен оттклуб с источником епг от яхан

## 4.11

- добавлен baltic.tv

## 4.10

- сделал сборку deb (надо протестировать)
- добавлен редирект на динамические ссылки для радуги, совок и другие для использования в букетах.
  Формат: http://localhost:9001/PROVIDER/CHANNEL_ID

## 4.9

- добавили новый иптв провайдер

## 4.8

- добавлено озо, миви, наше (спасибо freeuser)
- поддержка фуллшд скина
- запрещен повторный вход в плагин

## 4.7

- исправлен крэш при загрузке епг

## 4.6

- ввод букв в логин-пароль по синей кнопке
- исправлен крэш едема при отсутствии интернета
- добавлена радуга и телепром
- выход из плагина по кнопке экзит

## 4.5

- Поддержка избранных каналов
- Возможность выбора двух типов управления (enigma и neutrino)
- Улучшение интерфейса
- Исправление багов

## 4.4

- beta релиз

## 4.3

- Первая версия 4X


# *NO WARRANTIES.
*Authors are not responsible for the media streams content which one can access with this plugin.*
The plugin serves as an advanced media player.
The software provides graphical user interface to see teleguide and watch OTT media streams.
REST API implementation for specific media providers are contributed in the open source manner.
When using this plugin user is responsible to check that content from the corresponding provider
does not violate any international and local laws including copyright laws.
See `LICENSE` file for more info.


# *ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ.
*Авторы не несут ответственности за медиа потоки доступные через этот плагин.*
Плагин является медиаплеером с расширенными возможностями.
Это программное обеспечение предоставляет графический интерфейс для доступа к программе телепередач и OTT медиа потокам.
Имплементации REST API для конкретных медиа провайдеров вносятся в рамках проекта с открытым исходным кодом.
При использовании плагина пользователь должен удостоверится что медиа контент соответствующего провайдера
не нарушает международных и местных законов включая законы о защите авторских прав.
Смотрите файл `LICENSE` для более детальной информации.
