"use strict";

const table = document.querySelector("tbody");
const changePPRForm = document.querySelector("#change-ppr-form");
const changePPRFormPk = document.querySelector("#id_pk");
const changePPRFormDay = document.querySelector("#id_ppr_plan_day");
const changePPRFormEquipName = document.querySelector("#id_equip_name");

function editPPR(e) {
  const a = e.target.closest("a");
  if (a) {
    e.preventDefault();
    changePPRForm.style.display = "block";
    changePPRFormPk.value = a.dataset.pk;
    changePPRFormDay.value = a.dataset.ppr;
    changePPRFormEquipName.innerText = a.innerText
  }
}

changePPRForm.addEventListener("click", (e) => {
  if (!e.target.closest(".equipment_card")) {
    changePPRForm.style.display = "none";
  }
});

table.addEventListener("click", editPPR);

const shop_filter = document.querySelector("#id_shops");
const rows = Array.from(document.querySelectorAll("tbody tr"));

shop_filter.addEventListener("change", selectFilter);

function selectFilter() {
  rows.forEach((row) => {
    if ((this.value == 0) | (this.value == row.dataset.shop_id)) {
      row.style.display = "";
      row.dataset.filtered = "f";
    } else {
      row.style.display = "none";
      row.dataset.filtered = "";
    }
  });
}

selectFilter.bind(shop_filter)();

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
    if ((row.dataset.filtered == "f") & stringMatch(row, f)) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
}
