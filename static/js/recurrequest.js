
let curReqBanner = document.getElementById('currentRRHead');
// check for banner existence
if(curReqBanner !== null)
	curReqBanner.addEventListener('click', () => {curReqBanner.classList.add('closed');})

let lunchButton = document.getElementById("lunchButton");
let dinnerButton = document.getElementById("dinnerButton");
let activeMeal = "";
let activeDhalls = {};
let activeDays = {};
let dHallButtons = document.getElementsByClassName('dHallType');
let dayButtons = document.getElementsByClassName('dayType');
let anyDhallButton = document.getElementById('anyDhall');
let isAnyActive = false;
  let dayOptions = "";
  let dHallOptions = ""


function compareTimeStrings(t1, t2) {
	let hour1 = Number(t1.substring(0, 2));
	let hour2 = Number(t2.substring(0, 2));
	let min1 = Number(t1.substring(3));
	let min2 = Number(t2.substring(3));

	if (hour1 != hour2) return hour1 - hour2;
	else
		return min1 - min2;
};


for (btn of dHallButtons) {
	activeDhalls[btn.id] = false;
}


lunchButton.addEventListener('click', function onClick() {
	activeMeal = 'lunch';
	// console.log('lunch Pressed');
	lunchButton.style.backgroundColor = "#ff9f46";
	dinnerButton.style.backgroundColor = '';

});

dinnerButton.addEventListener('click', function onClick() {
	activeMeal = 'dinner';
	// console.log('dinner Pressed');
	dinnerButton.style.backgroundColor = "#ff9f46";
	lunchButton.style.backgroundColor = '';

});

// console.log("buttons "); // console.log(dayButtons);

for (btn of dHallButtons) {
	activeDhalls[btn.id] = false;
}

for (btn of dayButtons) {
	activeDays[btn.id] = false;
}

for (let i = 0; i < dayButtons.length; i++) {
	let btn = dayButtons[i];
	btn.addEventListener('click',
		function () {

			day = btn.id;

			// select Dhall
			if (!activeDays[day]) {
				btn.style.backgroundColor = "#ff9f46";
				activeDays[day] = true;
			}
			else {
				btn.style.backgroundColor = "";
				activeDays[day] = false;
			}

			
			// console.log(activeDays)

		});
}

for (day of dayButtons) {

// console.log('id is ' + day.id)
day.addEventListener('click', function ()
		{
		  const dayMap = {'Mon': "M", "Tues": "T", "Wed":"W", "Thurs":"R", "Fri": "F", "Sat":"S","Sun":"U"}
		  dayOptions = ""
		  for (var day in activeDays) {
			// console.log(day + 'is ' + activeDays[day])
			  if (activeDays[day]) {
				dayOptions += (dayMap[day]);
				
			  }
			}


		  // console.log('day field is ' + dayOptions);
		  document.getElementById('daysField').setAttribute('name', dayOptions);
		  // console.log("df is "+document.getElementById('daysField').getAttribute('name'))

		});
// console.log(day.id + "created")
}


	


for (let i = 0; i < dHallButtons.length; i++) {
	let btn = dHallButtons[i];
	btn.addEventListener('click',
		function () {

			dhall = btn.id;

			// select Dhall
			if (!activeDhalls[dhall]) {
				btn.style.backgroundColor = "#ff9f46";
				activeDhalls[dhall] = true;
			}
			else {
				btn.style.backgroundColor = "";
				activeDhalls[dhall] = false;
			}

			// deactivate anyDHall button
			if(isAnyActive)
			{
				anyDhallButton.style.backgroundColor = "";
				isAnyActive = false;
			
			}
			

			// console.log(activeDhalls)

		});

}



for (let i = 0; i < dHallButtons.length; i++) {
	  let btn = dHallButtons[i];

  btn.addEventListener('click', () =>
  {
	dHallOptions = "";
	for (var dh in activeDhalls) {
		if (activeDhalls[dh]) {
		  dHallOptions += (dh + "-");
		  dHallSelected = true;
		}
		// console.log(dHallOptions)

	  document.getElementById('hallType').setAttribute('name', dHallOptions);
	  // console.log('name is '+document.getElementById('hallType').getAttribute('name'));
	

	}

  });

}




anyDhallButton.addEventListener('click',
	function(){

		if(!isAnyActive)
			anyDhallButton.style.backgroundColor = "#ff9f46";
		else
			anyDhallButton.style.backgroundColor = "";
			
		for(let i = 0; i < dHallButtons.length; i++)
		{
			let btn = dHallButtons[i];
			
			// activate all buttons
			if(!isAnyActive)
				{
					activeDhalls[btn.id] = true;
					btn.style.backgroundColor = "#ff9f46";
				}
			else // deactivate all buttons
				{
					activeDhalls[btn.id] = false;
					btn.style.backgroundColor = "";
				}
		}
		// flip active flag
		isAnyActive = !isAnyActive;
	});



// update url to contain proper match request information
function updateUrl() {
	let url = "/submitrecurrequest"
	let startTime = document.getElementById("startTimeButton").value;
	let endTime = document.getElementById("endTimeButton").value;


	url += "?meal=" + activeMeal;
	url += "&location=";

	let dHallSelected = false;
	let dHallOptions = "";
	for (var dh in activeDhalls) {
		if (activeDhalls[dh]) {
			dHallOptions += (dh + "-");
			dHallSelected = true;
		}
	}

	// only update url if time, meal type, and location are all specified
	url += dHallOptions.slice(0, -1);
	url += "&start=" + startTime;
	url += "&end=" + endTime;
	url += "&days=" + dayOptions;
	url += "&atdhall=False";

	// console.log(url);

	submitButtonForm.setAttribute('href', url);
}


// return the length of time between t1 and t2 in minutes
function length(t1, t2) {
	let hour1 = Number(t1.substring(0, 2));
	let hour2 = Number(t2.substring(0, 2));
	let min1 = Number(t1.substring(3));
	let min2 = Number(t2.substring(3));

	let time1 = new Date();
	let time2 = new Date();
	time1.setHours(hour1);
	time1.setMinutes(min1);
	time2.setHours(hour2);
	time2.setMinutes(min2);

	let millis = time2.getTime() - time1.getTime();
	return millis / (1000 * 60);
}
function validateTimes(t1, t2, meal) {

	if (t1 === "" || t2 === "" || meal === "") return false;
	else {


		let now = new Date();
		let nowTime = now.toTimeString().substring(0, 5);


		// on Saturday or Sunday (weekends)
		// on weekends, brunch/lunch starts at 10AM
		let lunch_start;
		if (now.getDay() == 0 || now.getDay() == 6)
			lunch_start = "10:00";
		else // on weekdays, 11:30
			lunch_start = "11:30";

		// times are within lunch range and not in past
		let lunch_bool = (meal === 'lunch') &&
			(compareTimeStrings(lunch_start, t1) <= 0) &&
			(compareTimeStrings(t1, t2) < 0) &&
			(compareTimeStrings(t2, "14:00") <= 0);

		// times are within dinner range and not in past
		let dinner_bool = (meal === "dinner") &&
			(compareTimeStrings("17:00", t1) <= 0) &&
			(compareTimeStrings(t1, t2) < 0) &&
			(compareTimeStrings(t2, "20:00") <= 0);

		return lunch_bool || dinner_bool;
	}
}


// validate request fields, prevent submission if invalid
submitButtonForm.addEventListener('click', function (event) {

let startTime = document.getElementById("startTimeButton").value;
let endTime = document.getElementById("endTimeButton").value;
// console.log(startTime + " " + endTime);

// determine if any dhall buttons have been pressed 'ON'
let selected = false;
for (var dh in activeDhalls)
	if (activeDhalls[dh])
		selected = true;

// console.log('dHallselected' + selected)

// check if times are within the reasonable range and ordered correctly
let validMealTimes = validateTimes(startTime, endTime, activeMeal);
// console.log('valid mealtimes ' + validMealTimes)

let emptyFields = (endTime === "" || startTime === "" || activeMeal === "" || !selected || dayOptions == "")
// console.log('empty fields?: ' + emptyFields)

let interval_len = 20;
let longEnoughInterval = length(startTime, endTime) >= interval_len;
// console.log('long enough interval?: ' + longEnoughInterval)

	document.getElementById('errorBox').innerHTML = ""
	// takeout validMealTimes to remove lunch/dinner time validation
	if (emptyFields || !validMealTimes || !longEnoughInterval) {
		// console.log('attempt to send invalid meal request')
		// if there is an incomplete field, only show this error
		if (emptyFields)
			document.getElementById('errorBox').innerHTML += "<p>*Please enter all information to make a match request</p><br>"
		// otherwise, if times are not appropriate, prompt user to enter valid hours
		else if (!validMealTimes)
			{
				// var nowTimeStr = (new Date()).toLocaleTimeString('en-GB').substring(0,5);
				// if ((compareTimeStrings(nowTimeStr, "14:00") > 0 && activeMeal == 'lunch') || 
				// 	((compareTimeStrings(nowTimeStr, "20:00")  > 0) && activeMeal == 'dinner'))
				// 	document.getElementById('errorBox').innerHTML += "<p>*The hours of the selected mealtime have passed.<br> Please refer to the dining hall hours to enter valid times for a match request.</p><br>"
				// else
					document.getElementById('errorBox').innerHTML += "<p>*The dining hall may not be open for the selected meal at these hours.<br> Please refer to the dining hall hours to enter valid times for a match request.</p><br>"
			}


		// if time entered isn't long enough and all fields complete
		if (!longEnoughInterval && !emptyFields)
			document.getElementById('errorBox').innerHTML += "<p>*Please enter a time interval of at least " + interval_len + " minutes to make a request</p><br>"

		// prevents submission
		event.preventDefault();
	}
		else updateUrl();
});



	lunchButton.addEventListener('click', updateUrl);
	dinnerButton.addEventListener('click', updateUrl);

	for (let i = 0; i < dHallButtons.length; i++)
	dHallButtons[i].addEventListener('click', updateUrl)

	for (let i = 0; i < dayButtons.length; i++)
	dayButtons[i].addEventListener('click', updateUrl)

	let startTimeButton = document.getElementById("startTimeButton");
	let endTimeButton = document.getElementById("endTimeButton");
	startTimeButton.addEventListener('click', updateUrl);
	endTimeButton.addEventListener('click', updateUrl);
	// update url on changing times
	startTimeButton.addEventListener('change', updateUrl);
	endTimeButton.addEventListener('change', updateUrl)
	anyDhallButton.addEventListener('click', updateUrl);

