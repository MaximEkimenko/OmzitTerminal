let td_cell = document.getElementsByClassName("td_cell");
// переменные цветов
let color_fail = "red";
let color_ok = "MediumSeaGreen";
let color_not_ok = "IndianRed";
let color_master = "Orange";
let color_control_man = "Gold";
let color_progress = "Khaki";
// подкраска ячеек ожидания
for (let i = 0; i < td_cell.length; i++) {
    if (td_cell[i].innerText !== "утверждено") {
        td_cell[i].bgColor = color_not_ok;
    } else if (td_cell[i].innerText === "утверждено") {
        td_cell[i].bgColor = color_ok;
    }
}
