//const apiUrl = 'http://127.0.0.1:8090/'
const apiUrl = 'http://192.168.8.30:8000/'
let pathArray = window.location.pathname.split('/');
const wsNumber = pathArray[2]
let shiftTasks


document.addEventListener("DOMContentLoaded", (event) => {
    const initialTable = document.getElementById('main_table').innerHTML
    let shiftTasksTable = document.getElementById('main_table');
    shiftTasksTable.style.display = 'none'

    async function getShiftTasks () {
        shiftTasksTable.innerHTML = initialTable
        let shiftTasksUrl = new URL(`api/worker/${wsNumber}`, apiUrl);
        let response = await fetch(shiftTasksUrl);
        if (response.ok) {
            shiftTasks = await response.json();
            if (shiftTasks.length != 0) {
                shiftTasksTable.style.display = 'inline-block'
                // Создание строк
                for (let i = 0; i < shiftTasks.length; i++) {
                    await createShiftTaskRow(shiftTasks[i])
                }
                // Обновление цветов строк
                let rows = shiftTasksTable.getElementsByTagName('tr')
                for (let i = 1; i < rows.length; i++) {
                    await returnColor(rows[i])
                }
            } else {
                shiftTasksTable.style.display = 'none'
                document.getElementById("no-st").innerHTML = `Распределённые сменные задания на РЦ ${wsNumber} отсутствуют.`
            }


        }
    }

    async function returnColor(row) {
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

    // Создание строки
    async function createShiftTaskRow (shiftTask) {
        let row = document.createElement("tr");
        row.className = "table_row";

        for (let key in shiftTask) {
          let col = document.createElement("td");
          col.className = "td_cell";
          let col_p = document.createElement("p");
          col_p.className = "cell_text";
          if (shiftTask[key]) {
            col_p.innerHTML = shiftTask[key];
          } else {
            col_p.innerHTML = "-";
          }
          col.appendChild(col_p);
          row.appendChild(col);
        }
        shiftTasksTable.appendChild(row);
    }

    getShiftTasks()

    const countdown = document.getElementById("id_countdown");
    let currentRow = 0
    tr = shiftTasksTable.getElementsByTagName("tr");
    let timer = 30
    document.addEventListener("keydown", async function (event) {
        timer = 30
        if (event.code == 'ArrowUp' && currentRow > 1) {
            returnColor(tr[currentRow]);
            currentRow -= 1
            tr[currentRow].focus()
            tr[currentRow].bgColor = 'orange';
        }
        if (event.code == 'ArrowDown' && currentRow < tr.length - 1) {
            returnColor(tr[currentRow]);
            currentRow += 1
            tr[currentRow].focus()
            tr[currentRow].bgColor = 'orange';
        }

        // id выбранного option
        let shiftTaskRow = tr[currentRow].getElementsByTagName('td');
        // кнопка вызов мастера
        if (event.code == "KeyK") {

            let callMasterUrl = new URL(`api/call-master`, apiUrl);
            let data = {
                st_number: shiftTaskRow[0].children[0].innerHTML
            }
            let success = await postData(callMasterUrl, data)
            await getShiftTasks()
            if (success.is_called) {
              showAlert("Сообщение мастеру отправлено.")
            } else {
              showAlert("Не удалось вызвать мастера. Попробуйте еще раз!")
            }

        // кнопка вызов диспетчера
        } else if (event.code == "KeyX") {

            let callDispatcherUrl = new URL(`api/call-dispatcher`, apiUrl);
            let data = {
                st_number: shiftTaskRow[0].children[0].innerHTML
            }
            let success = await postData(callDispatcherUrl, data)
            await getShiftTasks()
            if (success.is_called) {
              showAlert("Сообщение диспетчеру отправлено.")
            } else {
              showAlert("Не удалось вызвать диспетчера. Попробуйте еще раз!")
            }

        }
        // кнопка запуск СЗ
        else if (event.code == "KeyC") {
            let jobStartUrl = new URL(`api/start-job`, apiUrl);
            let data = {
                st_number: shiftTaskRow[0].children[0].innerHTML
            }
            let success = await postData(jobStartUrl, data)
            await getShiftTasks()
            if (success.is_launched) {
               showAlert("Сменное задание запущенно в работу.")
            } else {
               showAlert('В работу может быть запущено СЗ только со статусами "запланировано" и "пауза".')
            }
        }

    })

    function showAlert (message) {
        const notification = document.getElementById("terminal_alert");
        notification.innerHTML = message
        notification.style.display = "block"
        notification.focus()
    }

    async function postData(url = '', data = {}) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        console.log(data)
        if (response.ok) {
            let json = await response.json()
            console.log(json)
            return json
        }
    }

    let x = setInterval(function() {
        timer -= 1
        countdown.innerHTML = 'Обновление списка сменных заданий через ' + timer + ' сек';
      if (timer == 0) {
        clearInterval(x);
        location.href = location.pathname;
      }
    }, 1000);
});
