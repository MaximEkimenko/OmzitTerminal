"use strict";
const addOrderButton = document.querySelector("#add_order_button"); // Получаем кнопки с классом
const equipmentForm = document.querySelector("#add-order-form");
const $deleteForm = document.querySelector("#delete-order-form");

const $table = document.querySelector("table");

// появление формы добавления заявки при нажатии на кнопку
// кнопка появляется только для админа и начальника цеха
if (addOrderButton) {
  addOrderButton.addEventListener("click", (e) => {
    equipmentForm.style.display = "block";
  });
}
// модальная форма добавления заявки пропадает , если кликнуть за ее пределами
equipmentForm.addEventListener("click", (e) => {
  if (!e.target.closest(".equipment_card")) {
    equipmentForm.style.display = "none";
  }
});

// применение фильтров из заголовков таблицы
const el = document.getElementById("filter_form");

function onChange() {
  document.getElementById("filter_form").submit();
}

//===========================================
//   удаление заявки
//===========================================
//нужно этой нопке по событию назначать id удаляемой заявке, чтобы потом через форму отправлять на сервер
const $commitDeleteButton = document.querySelector("#commit-delete-buton");
//ищем все кнопки удаления свежих заявок и подвешиваем на них событие появления модального окна для удалени
const $deleteButtons = $table.querySelectorAll("button[name='delete']");
$deleteButtons.forEach((element) => {
  element.addEventListener("click", (e) => {
    e.preventDefault();
    $commitDeleteButton.value = element.value;
    $deleteForm.style.display = "block";
  });
});

//===========================================
//     отмена удаления
const $cancelDeleteButton = document.querySelector("#cancel-delete-button");
// при нажатии на кнопку
$cancelDeleteButton.addEventListener(
  "click",
  (e) => ($deleteForm.style.display = "none")
);
// при нажатии вне формы
$deleteForm.addEventListener("click", (e) => {
  if (!e.target.closest(".add_to_plan")) {
    $deleteForm.style.display = "none";
  }
});

//===========================================
//   раскараска таблицы
//===========================================
const table_rows = document.getElementsByClassName("table_row");

const DETECTED = "1";
const START_REPAIR = "2";
const WAIT_FOR_MATERIALS = "3";
const WAIT_FOR_ACT = "4";
const REPAIRING = "5";
const FIXED = "6";
const ACCEPTED = "7";
const CANCELLED = "8";
const UNPRPAIRABLE = "9";

const status_cels = document.querySelectorAll(".status_name");

const statusColors = {
  DETECTED: "rgba(255, 25, 82, 0.3",
  START_REPAIR: "rgba(253, 68, 43, 0.3)",
  WAIT_FOR_MATERIALS: "rgba(255, 200, 47,  0.35)",
  WAIT_FOR_ACT: "rgba(214, 198, 53, 0.3)",
  ACCEPTED: "rgba(80, 200, 103, 0.3)",
  CANCELLED: "rgba(77, 72, 58, 0.3)",
  UNPRPAIRABLE: "rgba(119, 0, 80, 0.3)",
};

const color_DETECTED = "rgba(255, 25, 82, 0.3)";
const color_REPAIRING = "rgba(253, 68, 43, 0.3)";
const color_FIXED = "rgba(147, 201, 180, 0.3)";
const color_ACCEPTED = "rgba(80, 200, 103, 0.3)";
const color_WAIT_FOR_ACT = "rgba(214, 198, 53, 0.3)";
const color_UNPRPAIRABLE = "rgba(119, 0, 80, 0.3)";
const color_START_REPAIR = "rgba(253, 68, 43, 0.3)";
const color_WAIT_FOR_MATERIALS = "rgba(255, 200, 47,  0.35)";
const color_CANCELLED = "rgba(77, 72, 58, 0.3)";
const color_SUSPENDED = "rgba(252, 229, 153, 0.3)";

for (let i = 0; i < table_rows.length; i++) {
  let stat_cell = table_rows[i].querySelector(".status_name");
  switch (stat_cell.innerText) {
    case "требует ремонта":
      table_rows[i].style.background = color_DETECTED;
      break;
    case "в ремонте":
      table_rows[i].style.background = color_REPAIRING;
      break;
    case "ремонт окончен":
      table_rows[i].style.background = color_FIXED;
      break;
    case "ремонт принят":
      table_rows[i].style.background = color_ACCEPTED;
      break;
    case "ожидание акта":
      table_rows[i].style.background = color_WAIT_FOR_ACT;
      break;
    case "неремонтопригодно":
      table_rows[i].style.background = color_UNPRPAIRABLE;
      break;
    case "ремонт начат":
      table_rows[i].style.background = color_START_REPAIR;
      break;
    case "требуются материалы":
      table_rows[i].style.background = color_WAIT_FOR_MATERIALS;
      break;
    case "ремонт отменен":
      table_rows[i].style.background = color_CANCELLED;
      break;
    case "приостановлено":
      table_rows[i].style.background = color_SUSPENDED;
  }
}

//===========================================
// фильтрация оборудования при добавлении задания
//===========================================
let equipmentData = undefined;

//добавлем названия оборудования в выпадающий список
const $equipmentSelect = document.querySelector("#id_equipment");
equipFilterSelect();

// подключаем фильтры
const $shop_filter = document.querySelector("#id_shops");
const $name_filter = document.querySelector("#id_word_filter");

$shop_filter.addEventListener("change", () => {
  equipFilterSelect($shop_filter.value, $name_filter.value);
});
$name_filter.addEventListener("input", () => {
  equipFilterSelect($shop_filter.value, $name_filter.value);
});

async function getEquipmentData() {
  URL = `${window.location.origin}/orders/filter_data/`;
  const raw_data = await fetch(URL);
  const json_data = await raw_data.json();
  return json_data["filter"];
}

function create_option(entry, shop_id, textFragment) {
  if (
    ((shop_id == 0) | (entry.shop_id == shop_id)) &
    entry.unique_name.toLowerCase().includes(textFragment)
  ) {
    const $opt = new Option(entry.unique_name, entry.id);
    return $opt;
  }
}

// функция, которая фильтрует оборудование по местоположению или части текста
async function equipFilterSelect(shop_id = 0, textFragment = "") {
  if (!equipmentData) equipmentData = await getEquipmentData();
  $equipmentSelect.options.length = 0;
  for (let entry of equipmentData) {
    const $opt = create_option(entry, shop_id, textFragment);
    if ($opt) $equipmentSelect.options.add($opt);
  }
}

// это попытка сделать свою фильрацию по колонкам
// но как-то не получилось, что-то пошло не так
/*
function sortTable(cell) {
  console.log("sort");
  var table, rows, switching, i, x, y, shouldSwitch;
  table = document.getElementById("st_table");
  switching = true;
  while (switching) {
    switching = false;
    rows = table.rows;
    for (i = 1; i < rows.length - 1; i++) {
      shouldSwitch = false;
      x = rows[i].getElementsByTagName("TD")[cell];
      y = rows[i + 1].getElementsByTagName("TD")[cell];
      x = x.innerText;
      y = y.innerText;
      console.log(x,  y, x + y,  Number(x) + Number(y))
      if (isNaN(Number(x)) & isNaN(Number(y))) {
        x = Number(x);
        y = Number(y);
      } else {
        x = x.toLowerCase();
        y = y.toLowerCase();
      }

      //console.log(x, y, "x < y", x < y, x + y);
      if (x > y) {
        shouldSwitch = true;
        break;
      }
    }
    if (shouldSwitch) {
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
    }
  }
}


function sortTableHref(cell) {
  console.log("sort");
  var table, rows, switching, i, x, y, shouldSwitch;
  table = document.getElementById("st_table");
  switching = true;
  while (switching) {
    switching = false;
    rows = table.rows;
    for (i = 1; i < rows.length - 1; i++) {
      shouldSwitch = false;
      x = rows[i].getElementsByTagName("TD")[cell];
      y = rows[i + 1].getElementsByTagName("TD")[cell];
      x = x.children[0].innerText;
      y = y.children[0].innerText;

      xtemp = parseInt(x);
      ytemp = parseInt(y);
      if (xtemp & ytemp) {
        x = xtemp;
        y = ytemp;
      } else {
        x = x.toLowerCase();
        y = y.toLowerCase();
      }

      console.log(x, y);
      if (x > y) {
        shouldSwitch = true;
        break;
      }
    }
    if (shouldSwitch) {
      switching = true;
    }
  }
}
*/
