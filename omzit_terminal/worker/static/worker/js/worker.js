// Периодическая перезагрузка страницы
setTimeout(() => (location.href = location.pathname), 30000);
// функция отображения сообщения

// подкраска ячеек

let table_row = document.getElementsByClassName("table_row");

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
        table_row[i].style.color = "black";
    } else if (table_row[i].innerText.includes("принято")) {
        table_row[i].bgColor = color_ok;
    } else if (table_row[i].innerText.includes("простой")) {
        table_row[i].bgColor = color_fail;
    }
}
// подкраска ячеек ожидания
let td_cell = document.getElementsByClassName("td_cell");
console.log(td_cell);
for (let i = 0; i < td_cell.length; i++) {
    if (td_cell[i].innerText === "ожидание мастера") {
        td_cell[i].style.setProperty("background-color", color_master, "important");
        td_cell[i].style.color = "black";
        td_cell[i].style.setProperty("font-weight", "bold");
        //td_cell[i].bgColor = color_master;
    } else if (td_cell[i].innerText === "ожидание контролёра") {
        //td_cell[i].bgColor = color_control_man;
        td_cell[i].style.setProperty("background-color", color_control_man, "important");
        td_cell[i].style.color = "black";
        td_cell[i].style.setProperty("font-weight", "bold");
    } else if (td_cell[i].innerText === "пауза") {
        //td_cell[i].bgColor = color_control_man;
        td_cell[i].style.setProperty("background-color", color_master, "important");
        td_cell[i].style.color = "black";
        td_cell[i].style.setProperty("font-weight", "bold");
    } else if (
        td_cell[i].innerText === "брак" ||
        td_cell[i].innerText === "не принято" ||
        td_cell[i].innerText === "брак" ||
        td_cell[i].innerText === "принято"
    ) {
        td_cell[i].style.color = "black";
        td_cell[i].style.setProperty("font-weight", "bold");
        td_cell[i].style.setProperty("font-size", "24px");
    }
}
