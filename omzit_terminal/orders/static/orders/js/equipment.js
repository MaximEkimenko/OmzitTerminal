"use strict";

//===========================================================================
//    служит для обработки всплывающего окна для добавления оборудования
//===========================================================================
const addEquipmentButton = document.querySelector("#add_equipment_button"); // Получаем кнопки с классом
const equipmentForm = document.querySelector("#add-equipment-form");

addEquipmentButton.addEventListener("click", (e) => {
  equipmentForm.style.display = "block";
});

equipmentForm.addEventListener("click", (e) => {
  if (!e.target.closest(".equipment_card")) {
    equipmentForm.style.display = "none";
  }
});

const el = document.getElementById("filter_form");
console.log(el);
function onChange() {
  document.getElementById("filter_form").submit();
}

//===========================================================================
//    фильтрует содержимое строк таблице на основании полей ввода
//    по нескольким строкам
//===========================================================================
const inputs = [];
const headItems = document.querySelectorAll("thead th");

headItems.forEach((elem, index) => {
  const inputFilter = elem.querySelector("input");
  if (inputFilter) {
    inputFilter.dataset.colNum = index;
    inputs.push(inputFilter);
  }
});

const rows = Array.from(document.querySelectorAll("tbody tr"));

inputs.forEach((element) => {
  element.addEventListener("input", filledInputs);
});

function stringMatch(row, filters) {
  // отдельные ячейки ряда
  const tds = row.getElementsByTagName("td");
  //строки должны совпасть во всех ячейках, где фильтры непустые
  const matches = filters.every((flt) => {
    return tds[flt.dataset.colNum].textContent
      .toLowerCase()
      .includes(flt.value.toLowerCase());
  });
  return matches;
}

function filledInputs() {
  //сначала выбираем непустые фильтры, чтобы не делать сравнение по всем фильтрам
  const f = inputs.filter((element) => element.value != "");
  // пробегаемся по всем строкам таблицы и смотрим, чтобы содержимое заполненных фильтров
  // совпадало во всемя ячейками в строке, несовпадающие строки скрываем
  rows.forEach((row) => {
    if (stringMatch(row, f)) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}
