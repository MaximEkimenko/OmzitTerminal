const table_row = document.getElementsByClassName("table_row");
// переменные цветов
const color_fail = "red";
const color_ok = "MediumSeaGreen";
const color_not_ok = "IndianRed";
const color_master = "Orange";
const color_control_man = "Gold";
const color_progress = "Khaki";
//подкраска рядов
for (let i = 0; i < table_row.length; i++) {
    if (table_row[i].textContent.includes("запланировано") && !table_row[i].textContent.includes("не запланировано")) {
        table_row[i].style.color = color_progress;
    } else if (table_row[i].textContent.includes("принято")) {
        table_row[i].style.color = color_ok;
    } else if (table_row[i].innerText === "не принято" || table_row[i].innerText === "брак") {
        table_row[i].style.color = color_not_ok;
    } else if (table_row[i].innerText === "ожидание мастера") {
        table_row[i].style.color = color_master;
    } else if (table_row[i].innerText === "ожидание контролера") {
        table_row[i].style.color = color_master;
    }
}
