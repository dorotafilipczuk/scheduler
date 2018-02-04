const login = require("facebook-chat-api");

a = process.argv.slice(2);


console.log(a);

// Create simple echo bot
login({email: "dorota.test1@gmail.com", password: "b35tt3am"}, (err, api) => {
    if(err) {return console.error(err);}
    var options = {};
    for (var idx = 0; idx < a.length; ++idx) {
        options[a[idx]] = 0;
    }
    api.createPoll("Here is a list of dates I came up from your calendars. Suggest the best times.", '1812634275453572', options);
});
