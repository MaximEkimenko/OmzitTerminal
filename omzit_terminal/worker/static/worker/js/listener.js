// при перезагрузке страницы форма скрыта
let form = document.getElementById("sel_1");
form.style.display = "none";
// по нажатию кнопки вниз появляется форма
document.addEventListener("keydown", function (event) {
    if (event.code == "ArrowDown") {
        let form = document.getElementById("sel_1");
        form.style.display = "block";
        //фокус на объекте select
        let select_obj = document.getElementById("sel_3");
        select_obj.focus();
        // Исчезает через 10 секунд от последнего нажатия
        setTimeout(function () {
            let form = document.getElementById("sel_1");
            form.style.display = "none";
        }, 20000);
    }
});
