// Периодическая перезагрузка страницы
//setTimeout(() => (location.href = location.pathname), 30000);
// функция отображения сообщения

// подкраска ячеек

let table_row = document.getElementsByClassName("table_row");

for (let i = 0; table_row.length; i++) {
    returnColor(table_row[i])
}

function returnColor(row) {
    // переменные цветов

    let color_fail = "red";
    let color_ok = "MediumSeaGreen";
    let color_not_ok = "IndianRed";
    let color_master = "Orange";
    let color_control_man = "Gold";
    let color_progress = "Khaki";
    // Подкраска ряда
    row.bgColor = null
    if (row.innerText.includes("не принято")) {
        //console.log(td_cell[i].innerText;
        row.bgColor = color_not_ok;
    } else if (row.innerText.includes("брак")) {
        row.bgColor = color_fail;
    } else if (row.innerText.includes("в работе")) {
        row.bgColor = color_progress;
        row.style.color = "black";
    } else if (row.innerText.includes("принято")) {
        row.bgColor = color_ok;
    }
    // подкраска ячеек ожидания
    let td_cell = row.getElementsByTagName("td");
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
}

