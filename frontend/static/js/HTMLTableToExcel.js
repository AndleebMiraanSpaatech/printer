const HTMLTableToExcel = {

    table_to_book: ({ table, sheet }) => {
        const workbook = new ExcelJS.Workbook();
        const worksheet = workbook.addWorksheet(sheet);
        const trArr = $(table).find('tr').toArray();
        const cellMap = [], colWidth = [];

        trArr.forEach((tr, rowIdx) => {
            cellMap[rowIdx] = cellMap[rowIdx] || [];
            let colIdx = 0;

            $(tr).find('th,td').each((_, cell) => {
                while (cellMap[rowIdx][colIdx]) colIdx++;
                let value = cell.textContent.trim();
                if (value !== '' && !isNaN(value)) value = Number(value);

                const rowspan = parseInt(cell.getAttribute('rowspan') || 1);
                const colspan = parseInt(cell.getAttribute('colspan') || 1);

                const excelCell = worksheet.getCell(rowIdx + 1, colIdx + 1);
                excelCell.value = value;
                excelCell.alignment = { vertical: 'middle' };
                if (rowIdx === 0) excelCell.font = { bold: true };
                excelCell.border = { top: { style: 'thin' }, left: { style: 'thin' }, bottom: { style: 'thin' }, right: { style: 'thin' } };

                const len = value?.toString().length || 0;
                for (let c = 0; c < colspan; c++) colWidth[colIdx + c] = Math.max(colWidth[colIdx + c] || 0, len);

                for (let r = 0; r < rowspan; r++)
                    for (let c = 0; c < colspan; c++)
                        cellMap[rowIdx + r] = cellMap[rowIdx + r] || [], cellMap[rowIdx + r][colIdx + c] = 1;

                if (rowspan > 1 || colspan > 1) worksheet.mergeCells(rowIdx + 1, colIdx + 1, rowIdx + rowspan, colIdx + colspan);
                colIdx += colspan;
            });
        });

        worksheet.columns.forEach((col, i) => col.width = colWidth[i] + 2);
        return workbook;
    },

    download: ({ workbook, filename }) =>
        workbook.xlsx.writeBuffer().then(buf =>
            saveAs(new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }), filename)
        )

};
