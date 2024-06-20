const buttonDeletePopup = document.querySelector("#button_delete_popup"); // Получаем кнопки с классом
const deletePopup = document.querySelector("#confirm_delete_popup");
const buttonCancelDelete = document.querySelector("#cancel_delete_button");


buttonDeletePopup.addEventListener("click", (e) => {
  deletePopup.style.display = "block";
});
buttonCancelDelete.addEventListener("click", (e) => {
    deletePopup.style.display = "none";
  });
