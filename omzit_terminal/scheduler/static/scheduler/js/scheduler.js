const td_cell = document.getElementsByClassName("td_cell");

// переменные цветов
let color_fail = "red";
let color_ok = "MediumSeaGreen";
let color_not_ok = "IndianRed";
let color_master = "Orange";
let color_control_man = "Gold";
let color_progress = "Khaki";
let color_white = "white";
// подкраска ячеек
for (let i = 0; i < td_cell.length; i++) {
    // подкраска распределения
    if (td_cell[i].innerText === "не принято" || td_cell[i].innerText === "брак") {
        td_cell[i].style.color = color_fail;
    } else if (td_cell[i].innerText === "принято") {
        td_cell[i].style.color = color_ok;
    } else if (td_cell[i].innerText === "ожидание мастера") {
        td_cell[i].style.color = color_master;
    } else if (td_cell[i].innerText === "пауза") {
        td_cell[i].style.color = color_master;
    } else if (td_cell[i].innerText === "ожидание контролера") {
        td_cell[i].style.color = color_control_man;
    } else if (td_cell[i].innerText === "запланировано") {
        td_cell[i].style.color = color_white;
    } else if (td_cell[i].innerText === "в работе") {
        td_cell[i].style.color = color_progress;
    } else if (td_cell[i].innerText === "запрошено") {
        td_cell[i].style.color = color_not_ok;
    } else if (td_cell[i].innerText === "передано") {
        td_cell[i].style.color = color_not_ok;
    } else if (td_cell[i].innerText === "замечание") {
        td_cell[i].style.color = color_not_ok;
    } else if (td_cell[i].innerText === "утверждено") {
        td_cell[i].style.color = color_ok;
    } else {
        td_cell[i].bgColor = "white";
    }
}

function filterField(value, cell) {
  // Declare variables
  let filter, table, tr, td, i, txtValue;
  filter = value.toUpperCase();
  table = document.getElementById("st_table");
  tr = table.getElementsByTagName("tr");

  // Loop through all table rows, and hide those who don't match the search query
  for (i = 1; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[cell];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}

function sortTable(cell) {
 var table, rows, switching, i, x, y, shouldSwitch;
 table = document.getElementById("st_table");
 switching = true;
 /* Make a loop that will continue until
 no switching has been done: */
 while (switching) {
   // Start by saying: no switching is done:
   switching = false;
   rows = table.rows;
   /* Loop through all table rows (except the
   first, which contains table headers): */
   for (i = 1; i < (rows.length - 1); i++) {
     // Start by saying there should be no switching:
     shouldSwitch = false;
     /* Get the two elements you want to compare,
     one from current row and one from the next: */
     x = rows[i].getElementsByTagName("TD")[cell];
     y = rows[i + 1].getElementsByTagName("TD")[cell];
     // Check if the two rows should switch place:
     if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
       // If so, mark as a switch and break the loop:
       shouldSwitch = true;
       break;
     }
   }
   if (shouldSwitch) {
     /* If a switch has been marked, make the switch
     and mark that a switch has been done: */
     rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
     switching = true;
   }
 }
}