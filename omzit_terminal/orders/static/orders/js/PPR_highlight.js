"use strict";

const table_rows = Array.from(document.getElementsByClassName("table_row"));
const color_PPR = "rgba(25, 0, 255, 0.4)";
table_rows.forEach((row) => {
  let $ppr_cell = row.querySelector(".ppr_cell");
  if ($ppr_cell.dataset.ppr == "1") {
    $ppr_cell.style.background = color_PPR;
  }
});
