// Периодическая перезагрузка страницы
setTimeout(() => (location.href = location.pathname), 30000);
// функция отображения сообщения
function showNotification({ top = 0, right = 0, html }) {
    let notification = document.createElement("div");
    notification.className = "notification";
    notification.style.top = top + "px";
    notification.style.right = right + "px";
    notification.innerHTML = html;
    document.body.append(notification);
    setTimeout(() => notification.remove(), 10000);
}

// подкраска ячеек
let td_cell = document.getElementsByClassName("cell");
let table_row = document.getElementsByClassName("row");
// переменные цветов
let color_fail = "red";
let color_ok = "MediumSeaGreen";
let color_not_ok = "IndianRed";
let color_master = "Orange";
let color_control_man = "Gold";
let color_progress = "Khaki";
// Подкраска ряда
for (let i = 0; i < table_row.length; i++) {
    if (table_row[i].innerText.includes("не принято")) {
        //console.log(td_cell[i].innerText;
        table_row[i].bgColor = color_not_ok;
    } else if (table_row[i].innerText.includes("брак")) {
        table_row[i].bgColor = color_fail;
    } else if (table_row[i].innerText.includes("в работе")) {
        table_row[i].bgColor = color_progress;
    } else if (table_row[i].innerText.includes("принято")) {
        table_row[i].bgColor = color_ok;
    }
}
// подкраска ячеек ожидания
for (let i = 0; i < td_cell.length; i++) {
    if (td_cell[i].innerText.includes("ожидание мастера")) {
        td_cell[i].bgColor = color_master;
    } else if (td_cell[i].innerText.includes("ожидание контролёра")) {
        td_cell[i].bgColor = color_control_man;
    }
}
