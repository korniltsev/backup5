function openModal(header, body, successButton = false, status = false) {
    if (status) {
        $("#modal-status").html(status);
    }
    $("#modal-header").html(header);
    $("#modal-body").html(body);
    $("#modal-action").attr("onclick", successButton.action);
    if (successButton) {
        $("#modal-action").html(successButton.text).show();
    } else {
        $("#modal-action").hide();
    }
    $("#modal-name").show();
}

function closeModal() {
    $("#modal-status").html("");
    $("#modal-name").hide();
}

function showErrorModal(errors) {
    openModal("Some error occured!",
        "",
        false,
        errorListToHtml(errors));
}

function showSuccessModal(message, header) {
    openModal(header,
        "",
        false,
        message);
}

function insertErrorInModal(errors) {
    $("#modal-status").css("color", "red");
    if ($("#modal-name").is(":visible")) {
        $("#modal-status")
            .html(errorListToHtml(errors))
            .show()
            .delay(3000)
            .fadeOut();
    } else {
        showErrorModal(errors);
    }    
}

function insertSuccessInModal(message, header = "Success!") {
    $("#modal-status").css("color", "green");
    if ($("#modal-name").is(":visible")) {
        $("#modal-status")
            .html(message)
            .show()
            .delay(5000)
            .fadeOut();
    } else {
        showSuccessModal(message, header);
    }
}

function errorListToHtml(errors) {
    var errorsHtml = "<ul>";
    errors.forEach(function (err) {
        errorsHtml += "<li>" + err + "</li>";
    });
    errorsHtml += "</ul>";
    return errorsHtml;
}