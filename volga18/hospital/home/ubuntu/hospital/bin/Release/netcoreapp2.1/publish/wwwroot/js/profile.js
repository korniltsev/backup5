function loadView(viewName) {
    $("div[id^='view-']").each(function (i, view) {
        $(view).hide();
    });
    $("#view-" + viewName).show();
    switch (viewName) {
        case 'appointments':
            loadAppointments();
            break;
        case 'profile':
            loadProfile();
            break;
    }
}

function showAppointments(data) {
    var timeOptions = {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
    };
    var mainWidget = $("#view-appoinments-body");
    mainWidget.children().remove();
    mainWidget.show();

    var template = $("#template-appointment");
    if (data.length == 0) {
        var notFoundElem = "<p>You don't have any appointments</p>";
        mainWidget.append(notFoundElem);
        return false;
    }

    data.forEach(function (item, i, arr) {
        var newAppointment = template.clone();
        var dateTime = (new Date(item.DateTimeOfApp)).toLocaleString("en-US", timeOptions);
        if (item.Message != "") {
            newAppointment.find("#appointment-message")
                .find("a")[0]
                .setAttribute("href", "javascript:showAppMessage('"+btoa(item.Message)+"')");
        }  

        newAppointment.find("#appointment-time").html(dateTime); 
        newAppointment.find("#appointment-phone").html(item.Phone);
        newAppointment.find("#appointment-doctor").html(item.DoctorName);
        newAppointment.find("#appointment-doctor").attr("doctorid", item.DoctorId);
        newAppointment.find("#appointment-doctor").attr("appid", item.Id);
        newAppointment.attr("id", "appointment-" + item.Id);
        newAppointment.attr("id", "appointment-" + item.Id);
        mainWidget.append(newAppointment);
        newAppointment.show();
    });
}

function showAppMessage(message) {
    openModal("Your message is:", atob(message), false, false)
}

function loadAppointments() {  
    $.ajax({
        url: '/Appointment/Get',
        dataType: "json",
        success: function (data) {
            showAppointments(data);
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
}

function loadProfile() {
    var timeOptions = {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    };
    var mainWidget = $("#view-profile");

    $.ajax({
        url: '/Account/Get',
        dataType: "json",
        success: function (data, textStatus) {
            mainWidget.find("#profile-login").val(data.Login);
            mainWidget.find("#profile-name").val(data.Name);
            mainWidget.find("#profile-birth-date").val(
                new Date(data.DateOfBirth)
                    .toLocaleString("en-US", timeOptions));
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
}

function saveProfile() {
    var timeOptions = {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    };
    var form = $('#editProfileForm').serializeArray();
    var finalForm = {};
    form.forEach(function (item) {
        finalForm[item.name] = item.value;
    });
    $.ajax({
        url: '/Account/Edit',
        type: 'POST',
        data: JSON.stringify(finalForm),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function (data) {
            insertSuccessInModal("Profile has been edited.");
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
    return false;
}

function print(elem) {
    var appId = $(elem.parentElement.parentElement)
        .find("#appointment-doctor")[0]
        .getAttribute("appid");

    var win = window.open('/Appointment/Print/' + appId, '_blank');
    win.focus();
}

function repeatAppModal(elem) {
    var doctor = $(elem.parentElement.parentElement)
        .find("#appointment-doctor")[0];
        
    var header = "Repeat appointment";
    var body = "Input new date and time:";
    body += changeTimeBodyTemplate
        .replace("template-doctor-id", doctor.getAttribute("doctorid"))
        .replace("template-app-id", doctor.getAttribute("appid"));

    var successButton = {
        text: "Save",
        action: "saveRepeatApp()"
    };
    openModal(header, body, successButton, false);
}

function changeTimeModal(elem) {
    var doctor = $(elem.parentElement.parentElement)
        .find("#appointment-doctor")[0];

    var header = "Change time";
    var body = "Change time or date of your appointment:";
    body += changeTimeBodyTemplate
        .replace("template-doctor-id", doctor.getAttribute("doctorid"))
        .replace("template-app-id", doctor.getAttribute("appid"));

    var successButton = {
        text: "Change",
        action: "changeTimeApp()"
    };
    openModal(header, body, successButton, false);
}

function searchApp() {
    var formArray = $("#search-app-form").serializeArray();
    var finalForm = {};
    formArray.forEach(function (item) {
        finalForm[item.name] = item.value;
    });

    if (finalForm.FieldName == 'Date') {
        if (finalForm.Value == "") {
            finalForm.FieldName = 'DoctorName';
        } else {
            finalForm.Value = finalForm.Value.split(".")
                .reverse()
                .join("-");
            if ((new Date(finalForm.Value)) == "Invalid Date") {
                console.log('asd');
                insertErrorInModal(["Please, input valid Date"]);
                return false;
            }
        }
    }
    
    $.ajax({
        url: "/Appointment/GetByFilter",
        type: 'POST',
        data: JSON.stringify(finalForm),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function (response) {
            showAppointments(response);
        },
        error: function (xhr) {
            if (xhr.responseText) {
                var errors = [];
                JSON.parse(xhr.responseText).forEach(function (item) {
                    if (item.indexOf("was not recognized as a valid DateTime") > -1) {
                        errors.push("Please, input valid Date");
                    } else {
                        errors.push(item);
                    }
                });
                insertErrorInModal(errors);
            }
        }
    });
    return false;
}

changeTimeBodyTemplate = `
<div class="medilife-appointment-form">
    <form id="appointment-form" action="/">
        <div class="row align-items-end">
            <div class="col-12 col-md-6" >
                <div class="form-group">
                    <input type="date" doctorid=template-doctor-id 
                        onblur="loadTime(this.getAttribute('doctorid'))" class="form-control" name="date" 
                        id="appointment-date" placeholder="20.09.2018" required>
                </div>
                <div class="form-group">
                    <input type="hidden" name="Id" value="template-app-id" required>
                </div>
           </div>
           <div class="col-12 col-md-4">
                <div class="form-group">
                    <select class="form-control" id="time" name="time" required></select>
                </div>
           </div>
        </div>
    </form>
</div>
    `;
loadProfile();