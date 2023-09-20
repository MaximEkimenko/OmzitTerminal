let td_cell = document.getElementsByClassName("td_element");
// переменные цветов
let color_fail = "red";
let color_ok = "MediumSeaGreen";
let color_not_ok = "IndianRed";
let color_master = "Orange";
let color_control_man = "Gold";
let color_progress = "Khaki";
// подкраска ячеек ожидания
for (let i = 0; i < td_cell.length; i++) {
    if (td_cell[i].innerText === "не принято" || td_cell[i].innerText === "брак") {
        td_cell[i].bgColor = color_not_ok;
    } else if (td_cell[i].innerText === "принято") {
        td_cell[i].bgColor = color_ok;
    } else if (td_cell[i].innerText === "ожидание мастера") {
        td_cell[i].bgColor = color_master;
    } else if (td_cell[i].innerText === "ожидание контролера") {
        td_cell[i].bgColor = color_control_man;
    } else if (td_cell[i].innerText === "запланировано") {
        td_cell[i].bgColor = color_progress;
    }
}