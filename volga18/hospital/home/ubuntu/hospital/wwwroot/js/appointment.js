function setCurrentDoctorId(doctorId) {
    $($("select#doctor")
        .next()
        .find("span.current")[0])
        .attr("id", doctorId);
    removeTime();
}

function removeTime() {
    var time = $("select#time");
    time.children().remove();
    $(time.next().find("ul")[0]).children().remove();
    $(time.next().find("span.current")[0]).html("");
}

function removeDoctors(doctors, doctorsUl) {
    doctors.children().remove();
    doctorsUl.children().remove();
    removeTime();
}

function loadDoctors(specId) {
    $.ajax({
        url: "/Staff/GetDoctors",
        type: 'POST',
        data: JSON.stringify(specId),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function (response) {
            var doctors = $("select#doctor");
            var doctorsUl = $(doctors.next().find("ul")[0]);

            //clear lists
            removeDoctors(doctors, doctorsUl);

            $.each(response, function () {
                doctors.append("<option value=" + this.Id + ">" + this.Name + "</option>");
                doctorsUl.append('<li class="option" onclick="setCurrentDoctorId(' +
                    this.Id + ')" data-value="' + this.Name + '">' +
                    this.Name + '</li >');
            });
            $(doctors.next().find("span.current")[0]).html(response[0].Name);
            $(doctors.next().find("span.current")[0]).attr("id", response[0].Id);
            doctorsUl.find("li")[0].classList.add('selected');
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
}

function loadSpecialities() {
    $.ajax({
        url: "/Staff/GetSpecialities",
        success: function (response) {
            var specialities = $("select#speciality");
            var specialitiesUl = $(specialities.next().find("ul")[0]);
            $.each(response, function () {
                specialities.append("<option value=" + this.Id + ">" + this.Name + "</option>");
                specialitiesUl.append('<li onclick="loadDoctors(' +
                    this.Id + ')" class="option" data-value="' +
                    this.Name + '">' +
                    this.Name + '</li >');
            });
            $(specialities.next().find("span.current")[0]).html(response[0].Name);
            specialitiesUl.find("li")[0].classList.add('selected');
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
}

$("#appointment-date").focusout(function () {
    loadTime();
});

function loadTime(selectedDoctorId = false) {
    var date = $("#appointment-date").val();
    var isDateValid = true;
    if (date.length > 0) {
        date = date.split(".").reverse().join("-");
        if ((new Date(date)) == "Invalid Date") {
            isDateValid = false;
        } else {
            date = date + "T00:00:00";
        }
    } else {
        isDateValid = false;
    }
    removeTime();
    if (!isDateValid) {
        return -1;
    }

    if (selectedDoctorId) {
        doctorId = selectedDoctorId;
    } else {
        doctorId = $($("select#doctor")
            .next()
            .find("span.current")[0])
            .attr("id");
    }

    data = {
        "DateTimeOfApp": date,
        "DoctorId": doctorId
    }
    $.ajax({
        url: "/Appointment/GetFreeTime",
        type: 'POST',
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function (response) {
            var time = $("select#time");
            var timeUl = $(time.next().find("ul")[0]);
            $.each(response, function () {
                item = this.slice(0, -3);
                time.append("<option value=" + item + ">" + item + "</option>");
                timeUl.append('<li class="option" data-value="' +
                    item + '">' +
                    item + '</li>');
            });
            $(time.next().find("span.current")[0]).html(response[0].slice(0,-3));
            timeUl.find("li")[0].classList.add('selected');
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
}

function createAnAppointment() {
    var formArray = $("#appointment-form").serializeArray();
    var finalForm = {};
    formArray.forEach(function (item) {
        finalForm[item.name] = item.value;
    });
    if (finalForm.Phone == "" ||
        finalForm.date == "" ||
        finalForm.time == "" || typeof finalForm.time === "undefined") {
        insertErrorInModal(["Fill required fields: Phone, Date, Time"]);
        return false;
    }
        
    var date = finalForm.date.split(".")
        .reverse()
        .join("-");
    finalForm.DoctorId = $($("select#doctor")
        .next()
        .find("span.current")[0])
        .attr("id");
    finalForm.DoctorName = $($("select#doctor")
        .next()
        .find("span.current")[0])
        .html();
    finalForm.DateTimeOfApp = date + "T" + finalForm.time + ":00";
    delete finalForm.date;
    delete finalForm.time;
    delete finalForm.speciality;
    $.ajax({
        url: "/Appointment/Create",
        type: 'POST',
        data: JSON.stringify(finalForm),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function (response) {
            removeTime();
            insertSuccessInModal("Your appointment has been created.");
            loadTime();
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
    return false;
}

function saveRepeatApp() {
    var doctorId = $("input#appointment-date").attr("doctorid");
    var formArray = $("#appointment-form").serializeArray();
    var finalForm = {};
    formArray.forEach(function (item) {
        finalForm[item.name] = item.value;
    });
    if (finalForm.date == "" ||
        finalForm.time == "" || typeof finalForm.time === "undefined")
        return false;
    var date = finalForm.date.split(".")
        .reverse()
        .join("-");
    
    finalForm.DateTimeOfApp = date + "T" + finalForm.time + ":00";
    delete finalForm.date;
    delete finalForm.time;
    $.ajax({
        url: "/Appointment/Repeat",
        type: 'POST',
        data: JSON.stringify(finalForm),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function (response) {
            removeTime();
            insertSuccessInModal("New appointment has been created.");
            loadTime(doctorId);
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
    return false;
}

function changeTimeApp() {
    var doctorId = $("input#appointment-date").attr("doctorid");
    var formArray = $("#appointment-form").serializeArray();
    var finalForm = {};
    formArray.forEach(function (item) {
        finalForm[item.name] = item.value;
    });
    if (finalForm.date == "" ||
        finalForm.time == "" || typeof finalForm.time === "undefined")
        return false;
    var date = finalForm.date.split(".")
        .reverse()
        .join("-");

    finalForm.DateTimeOfApp = date + "T" + finalForm.time + ":00";
    delete finalForm.date;
    delete finalForm.time;
    $.ajax({
        url: "/Appointment/ChangeDateTime",
        type: 'POST',
        data: JSON.stringify(finalForm),
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        success: function (response) {
            removeTime();
            insertSuccessInModal("Your appointment has been rescheduled.");
            loadTime(doctorId);
        },
        error: function (xhr) {
            if (xhr.responseText) {
                insertErrorInModal(JSON.parse(xhr.responseText));
            }
        }
    });
    return false;
}