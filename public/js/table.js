function createTable(students) {
    var parsed = JSON.parse(students);

    var checkIfExists = document.getElementById("tableDiv");

    if(document.body.contains(checkIfExists)) {
        document.body.remove(checkIfExists);
    }

    var overallDiv = document.createElement("div");
    overallDiv.setAttribute('id', 'tableDiv')

    var headerDiv = document.createElement("div");
    headerDiv.setAttribute("class" , "tbl-header");

    var firstTable = document.createElement("table");
    firstTable.cellPadding = 0;
    firstTable.cellSpacing = 0;
    firstTable.border = 0;

    var tableHeader = document.createElement("thead");
    var headerRow = document.createElement("tr");

    var headerName = document.createElement("th");
    var text1 = document.createTextNode("Name");
    headerName.appendChild(text1);


    var headerYear = document.createElement("th");
    var text2 = document.createTextNode("Graduation Year");
    headerYear.appendChild(text2);

    var headerCertificationLevel = document.createElement("th");
    var text3 = document.createTextNode("Certification Level");
    headerCertificationLevel.appendChild(text3);

    headerRow.appendChild(headerName);
    headerRow.appendChild(headerYear);
    headerRow.appendChild(headerCertificationLevel);

    tableHeader.appendChild(headerRow);

    firstTable.appendChild(tableHeader);

    headerDiv.appendChild(firstTable);

    var bodyDiv = document.createElement("div");
    bodyDiv.setAttribute("class" , "tbl-content");

    var secondTable = document.createElement("table");
    firstTable.cellPadding = 0;
    firstTable.cellSpacing = 0;
    firstTable.border = 0;

    var tableBody = document.createElement("tbody");

    for(var i = 0; i < parsed.length; i++) {
        var tr = document.createElement("tr");

        var td1 = document.createElement("td");
        var td2 = document.createElement("td");
        var td3 = document.createElement("td");

        var text1 = document.createTextNode(parsed[i].username);
        var text2 = document.createTextNode(parsed[i].gradYear) //PLACE HOLDER
        var text3 = document.createTextNode(parsed[i].certLevel) //PLACE HOLDEr

        td1.appendChild(text1);
        td2.appendChild(text2);
        td3.appendChild(text3);

        tr.appendChild(td1);
        tr.appendChild(td2);
        tr.appendChild(td3);

        tableBody.appendChild(tr);
    }

    secondTable.appendChild(tableBody);
    bodyDiv.appendChild(secondTable);

    overallDiv.appendChild(headerDiv);
    overallDiv.appendChild(bodyDiv);

    document.body.appendChild(overallDiv);

}