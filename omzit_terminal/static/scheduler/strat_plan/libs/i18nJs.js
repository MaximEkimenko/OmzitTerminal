/*
 Copyright (c) 2012-2017 Open Lab
 Permission is hereby granted, free of charge, to any person obtaining
 a copy of this software and associated documentation files (the
 "Software"), to deal in the Software without restriction, including
 without limitation the rights to use, copy, modify, merge, publish,
 distribute, sublicense, and/or sell copies of the Software, and to
 permit persons to whom the Software is furnished to do so, subject to
 the following conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

function dateToRelative(localTime) {
    var diff = new Date().getTime() - localTime
    var ret = ''

    var min = 60000
    var hour = 3600000
    var day = 86400000
    var wee = 604800000
    var mon = 2629800000
    var yea = 31557600000

    if (diff < -yea * 2) ret = 'in ## years'.replace('##', (-diff / yea).toFixed(0))
    else if (diff < -mon * 9) ret = 'in ## months'.replace('##', (-diff / mon).toFixed(0))
    else if (diff < -wee * 5) ret = 'in ## weeks'.replace('##', (-diff / wee).toFixed(0))
    else if (diff < -day * 2) ret = 'in ## days'.replace('##', (-diff / day).toFixed(0))
    else if (diff < -hour) ret = 'in ## hours'.replace('##', (-diff / hour).toFixed(0))
    else if (diff < -min * 35) ret = 'in about one hour'
    else if (diff < -min * 25) ret = 'in about half hour'
    else if (diff < -min * 10) ret = 'in some minutes'
    else if (diff < -min * 2) ret = 'in few minutes'
    else if (diff <= min) ret = 'just now'
    else if (diff <= min * 5) ret = 'few minutes ago'
    else if (diff <= min * 15) ret = 'some minutes ago'
    else if (diff <= min * 35) ret = 'about half hour ago'
    else if (diff <= min * 75) ret = 'about an hour ago'
    else if (diff <= hour * 5) ret = 'few hours ago'
    else if (diff <= hour * 24) ret = '## hours ago'.replace('##', (diff / hour).toFixed(0))
    else if (diff <= day * 7) ret = '## days ago'.replace('##', (diff / day).toFixed(0))
    else if (diff <= wee * 5) ret = '## weeks ago'.replace('##', (diff / wee).toFixed(0))
    else if (diff <= mon * 12) ret = '## months ago'.replace('##', (diff / mon).toFixed(0))
    else ret = '## years ago'.replace('##', (diff / yea).toFixed(0))

    return ret
}

//override date format i18n

Date.monthNames = [
    'Январь',
    'Феврадль',
    'Март',
    'Апрель',
    'Май',
    'Июнь',
    'Июль',
    'Август',
    'Сентябрь',
    'Октябрь',
    'Ноябрь',
    'Декабрь',
]
// Month abbreviations. Change this for local month names
Date.monthAbbreviations = [
    'Янв',
    'Фев',
    'Март',
    'Апр',
    'Май',
    'Июн',
    'Июл',
    'Авг',
    'Сент',
    'Окт',
    'Ноя',
    'Дек',
]
// Full day names. Change this for local month names
Date.dayNames = ['Воскесенье', 'Понедельник', 'Вторник', 'Среда', 'Четеврг', 'Пятница', 'Суббота']
// Day abbreviations. Change this for local month names
Date.dayAbbreviations = ['ВС', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ']
// Used for parsing ambiguous dates like 1/2/2000 - default to preferring 'American' format meaning Jan 2.
// Set to false to prefer 'European' format meaning Feb 1
Date.preferAmericanFormat = false

Date.firstDayOfWeek = 0
Date.defaultFormat = 'd.M.yyyy'
Date.masks = {
    fullDate: 'EEEE, MMMM d, yyyy',
    shortTime: 'h:mm a',
}
Date.today = 'Сегодня'

Number.decimalSeparator = '.'
Number.groupingSeparator = ','
Number.minusSign = '-'
Number.currencyFormat = '###,##0.00'

var millisInWorkingDay = 28800000
var workingDaysPerWeek = 5

function isHoliday(date) {
    var friIsHoly = false
    var satIsHoly = false
    var sunIsHoly = false

    var pad = function (val) {
        val = '0' + val
        return val.substr(val.length - 2)
    }

    var holidays = '##'

    var ymd =
        '#' + date.getFullYear() + '_' + pad(date.getMonth() + 1) + '_' + pad(date.getDate()) + '#'
    var md = '#' + pad(date.getMonth() + 1) + '_' + pad(date.getDate()) + '#'
    var day = date.getDay()

    return (
        (day == 5 && friIsHoly) ||
        (day == 6 && satIsHoly) ||
        (day == 0 && sunIsHoly) ||
        holidays.indexOf(ymd) > -1 ||
        holidays.indexOf(md) > -1
    )
}

var i18n = {
    YES: 'Да',
    NO: 'Нет',
    FLD_CONFIRM_DELETE: 'удалить?',
    INVALID_DATA: 'Неверный формат даты',
    ERROR_ON_FIELD: 'ошибка поля',
    OUT_OF_BOUDARIES: 'Out of field admitted values:',
    CLOSE_ALL_CONTAINERS: 'Закрыть все?',
    DO_YOU_CONFIRM: 'Подвтерждаете?',
    ERR_FIELD_MAX_SIZE_EXCEEDED: 'достигнкт максимальный раземр поля',
    WEEK_SHORT: 'Н.',

    FILE_TYPE_NOT_ALLOWED: 'Неверный формат файла.',
    FILE_UPLOAD_COMPLETED: 'Файл загружен.',
    UPLOAD_MAX_SIZE_EXCEEDED: 'Достигнут максимальный размер файла',
    ERROR_UPLOADING: 'Ошибка загрузки',
    UPLOAD_ABORTED: 'Загрузка отменена',
    DROP_HERE: 'Перетащите файлы сюда',

    FORM_IS_CHANGED: 'На странице есть несохранённые данные!',

    PIN_THIS_MENU: 'PIN_THIS_MENU',
    UNPIN_THIS_MENU: 'UNPIN_THIS_MENU',
    OPEN_THIS_MENU: 'OPEN_THIS_MENU',
    CLOSE_THIS_MENU: 'CLOSE_THIS_MENU',
    PROCEED: 'Продолжить?',

    PREV: 'Пред.',
    NEXT: 'След.',
    HINT_SKIP: 'Закрыть подсказку.',

    WANT_TO_SAVE_FILTER: 'сохоаниьт фильтр',
    NEW_FILTER_NAME: 'новое имя фильтра',
    SAVE: 'Сохранить',
    DELETE: 'Удалить',
    HINT_SKIP: 'Закрыть подсказку.',

    COMBO_NO_VALUES: 'no values available...?',

    FILTER_UPDATED: 'Filter updated.',
    FILTER_SAVED: 'Filter correctly saved.',
}
