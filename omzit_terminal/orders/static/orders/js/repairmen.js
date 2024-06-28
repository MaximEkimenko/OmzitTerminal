"use strict";
//===========================================
//   удаление карточки
//===========================================
//нужно этой нопке по событию назначать id удаляемой заявке, чтобы потом через форму отправлять на сервер
const $commitDeleteButton = document.querySelector("#commit-delete-button");
//ищем все кнопки удаления свежих заявок и подвешиваем на них событие появления модального окна для удалени
const $beleteButtons = document.querySelectorAll(
  "button[name='delete_button']"
);
const $deleteForm = document.querySelector("#delete-shop-form");



$beleteButtons.forEach((element) => {
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
