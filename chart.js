google.charts.load('current', {'packages':['corechart']});
    google.charts.setOnLoadCallback(drawChart);

    function drawChart() {

      var data = new google.visualization.DataTable();
      data.addColumn('datetime', 'Time of Day');
      data.addColumn('number', 'Motivation Level');

      var myTableArray = [];

      $("table#samplestable tr").each(function() {
          var arrayOfThisRow = [];
          var tableData = $(this).find('td');
          if (tableData.length > 0) {
              tableData.each(function() { arrayOfThisRow.push($(this).text()); });
              myTableArray.push(arrayOfThisRow);
          }
      });
      console.log(myTableArray);
      var rows = [];
      myTableArray.forEach( x => {
        rows.push([new Date(x[1]),Number(x[0])]);
      })

      console.log(rows);

      data.addRows(rows);

      var options = {
        /*width: 900,*/
        height: 600,
        legend: {position: 'none'},
        enableInteractivity: false,
        chartArea: {
          width: '85%'
        },
        hAxis: {
          viewWindow: {
            min: new Date(myTableArray[0][1]),
            max: new Date(myTableArray[myTableArray.length-1][1])
          },
          gridlines: {
            count: -1,
            units: {
              days: {format: ['MMM dd']},
              hours: {format: ['HH:mm', 'ha']},
            }
          },
          minorGridlines: {
            units: {
              hours: {format: ['hh:mm:ss a', 'ha']},
              minutes: {format: ['HH:mm a Z', ':mm']}
            }
          }
        }
      };

      var chart = new google.visualization.LineChart(
        document.getElementById('chart_div'));

      chart.draw(data, options);

      /*var button = document.getElementById('change');
      var isChanged = false;

      button.onclick = function () {
        if (!isChanged) {
          options.hAxis.viewWindow.min = new Date(2015, 0, 1);
          options.hAxis.viewWindow.max = new Date(2015, 0, 1, 3);
          isChanged = true;
        } else {
          options.hAxis.viewWindow.min = new Date(2014, 11, 31, 18),
          options.hAxis.viewWindow.max = new Date(2015, 0, 3, 1)
          isChanged = false;
        }
        chart.draw(data, options);
      };*/
    }