mod data;

use itertools::Itertools;
use rand::seq::SliceRandom;
use rand::thread_rng;
use reqwest::{header, Client};
use structopt::StructOpt;

use std::sync::Arc;
use std::time::{Duration, SystemTime};

// Maximum response time in ms
const MAX_RESPONSE: u128 = 400;

#[derive(StructOpt)]
#[structopt(name = "coin-spewer")]
struct Args {
    #[structopt(short, long, help = "Endpoint to post to in the form http://<host>:<port>/<endpoint>")]
    endpoint: String,
    #[structopt(short, long, default_value = "1000", help = "Number of tasks to send")]
    requests: u64,
    #[structopt(short, long, default_value = "4", help = "Number of coins per task")]
    permutations: u8,
    #[structopt(short, long, default_value = "400", help = "Delay between task requests in milliseconds")]
    delay: u64,
}

#[tokio::main]
async fn main() {
    let Args {
        endpoint,
        requests,
        permutations,
        delay,
    } = Args::from_args();

    let mut rng = thread_rng();
    let client = Arc::new(reqwest::Client::new());

    println!("Starting...");
    let mut all_coins: Vec<String> = data::ALL_COINS.lines().map(|s| s.to_owned()).collect();
    all_coins.shuffle(&mut rng);
    let result = futures::future::try_join_all(
        all_coins
            .into_iter()
            .permutations(permutations as usize)
            .take(requests as usize)
            .enumerate()
            .map(|(i, mut coins)| {
                let (json, wrong) = (rand::random(), rand::random());

                if wrong {
                    // choose a random index
                    let idx = (0..coins.len())
                        .collect::<Vec<usize>>()
                        .choose(&mut rng)
                        .unwrap()
                        .clone();
                    // randomize that coin name
                    let mut chars = coins[idx].chars().collect::<Vec<char>>();
                    chars.shuffle(&mut rng);
                    coins[idx] = chars.into_iter().collect();
                }

                let body = if json {
                    serde_json::to_vec(&serde_json::json!({ "coins": coins })).unwrap()
                } else {
                    coins.insert(0, "coins".to_string());
                    coins.join("\n").into_bytes()
                };

                let mut headers = reqwest::header::HeaderMap::new();
                let content_type = if json { "application/json" } else { "text/csv" };
                headers.insert(header::CONTENT_TYPE, content_type.parse().unwrap());

                // Spawn so that we do not block waiting for the response
                let handle = tokio::spawn(send_task(
                    Arc::clone(&client),
                    endpoint.clone(),
                    headers,
                    i,
                    requests,
                    body,
                ));

                std::thread::sleep(Duration::from_millis(delay));
                handle
            }),
    )
    .await;

    match result {
        Ok(_) => println!("All tasks sent"),
        Err(e) => {
            println!("{}", e);
            std::process::exit(1)
        }
    }
}

async fn send_task(
    client: Arc<Client>,
    endpoint: String,
    headers: header::HeaderMap,
    iteration: usize,
    requests: u64,
    body: Vec<u8>,
) -> Result<(), String> {
    println!("Sending task {}/{}", iteration + 1, requests);

    let start = SystemTime::now();
    let res = client
        .post(&endpoint)
        .headers(headers)
        .body(body)
        .send()
        .await;

    match res {
        Ok(_) => println!("Task {}/{} sent", iteration + 1, requests),
        Err(e) => return Err(format!("Failed to send task to {}: {}", endpoint, e)),
    }

    let end = SystemTime::now().duration_since(start).unwrap();

    if end.as_millis() > MAX_RESPONSE {
        return Err(format!(
            "Failed! Response took {}ms. Maximum {}ms response.",
            end.as_millis(),
            MAX_RESPONSE
        ));
    }

    Ok(())
}
