const addEquipmentButton = document.querySelector("#add_equipment_button"); // Получаем кнопки с классом
const equipmentForm = document.querySelector("#add-equipment-form");
console.log(equipmentForm);

addEquipmentButton.addEventListener("click", (e) => {
  equipmentForm.style.display = "block";
});

equipmentForm.addEventListener("click", (e) => {
  if (!e.target.closest(".add_to_plan")) {
    equipmentForm.style.display = "none";
  }
});

const el = document.getElementById("filter_form");
console.log(el);
function onChange() {
  document.getElementById("filter_form").submit();
}
