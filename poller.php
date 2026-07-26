<?php
/**
 * Polling runner for the Telegram bot.
 * يجيب الرسايل الجديدة من تيليجرام (getUpdates) ويشغل ملف md.php
 * لكل رسالة بالظبط زي ما كان بيحصل مع الـ webhook، من غير ما نلمس كود md.php خالص.
 */

$token = "8783476618:AAHZHrmDXrEHqcFN24kbkEfoKc4wUAtDdbE"; // نفس التوكن اللي في md.php

$baseDir   = __DIR__;
$offsetFile = $baseDir . "/offset.txt";
$mdFile     = $baseDir . "/md.php";

// 1) نتأكد الـ webhook متلغي، عشان ميحصلش تعارض مع getUpdates
file_get_contents("https://api.telegram.org/bot{$token}/deleteWebhook");

// 2) نجيب آخر offset اتخزن من المرة اللي فاتت
$offset = 0;
if (file_exists($offsetFile)) {
    $offset = (int) trim(file_get_contents($offsetFile));
}

// 3) نجيب الرسايل الجديدة بس (اللي بعد الـ offset ده)
$url = "https://api.telegram.org/bot{$token}/getUpdates?timeout=0&offset={$offset}";
$response = @file_get_contents($url);

if ($response === false) {
    fwrite(STDERR, "تعذر الاتصال بتيليجرام\n");
    exit(1);
}

$data = json_decode($response, true);

if (!$data || empty($data['ok'])) {
    fwrite(STDERR, "رد غير متوقع من تيليجرام: {$response}\n");
    exit(1);
}

$updates = $data['result'];

if (empty($updates)) {
    echo "مفيش رسايل جديدة.\n";
    exit(0);
}

echo "لقيت " . count($updates) . " رسالة جديدة.\n";

foreach ($updates as $update) {
    $updateId = $update['update_id'];
    $json = json_encode($update);

    // نشغل md.php ونديله الـ update ده عن طريق stdin
    // (php://input في md.php بيقرا من stdin لما يتشغل من الـ CLI)
    $descriptors = [
        0 => ['pipe', 'r'], // stdin
        1 => ['pipe', 'w'], // stdout
        2 => ['pipe', 'w'], // stderr
    ];

    $process = proc_open('php ' . escapeshellarg($mdFile), $descriptors, $pipes, $baseDir);

    if (is_resource($process)) {
        fwrite($pipes[0], $json);
        fclose($pipes[0]);

        $stdout = stream_get_contents($pipes[1]);
        $stderr = stream_get_contents($pipes[2]);
        fclose($pipes[1]);
        fclose($pipes[2]);

        proc_close($process);

        echo "تم تنفيذ الرسالة رقم {$updateId}\n";
        if (!empty($stderr)) {
            fwrite(STDERR, "خطأ في الرسالة {$updateId}: {$stderr}\n");
        }
    } else {
        fwrite(STDERR, "فشل تشغيل md.php للرسالة {$updateId}\n");
    }

    // نحدث الـ offset بعد كل رسالة عشان لو حصل قطع منكملش من الأول
    $offset = $updateId + 1;
    file_put_contents($offsetFile, $offset);
}

echo "خلصت. آخر offset اتسجل: {$offset}\n";
