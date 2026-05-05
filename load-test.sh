#!/bin/bash
echo "🚀 Memulai Load Test ke http://localhost:30001"
echo "Tekan [CTRL+C] untuk berhenti."

# Gunakan ab (Apache Benchmark) atau loop curl sederhana
# Di sini kita pakai loop curl paralel agar mudah dijalankan tanpa install tools tambahan
for i in {1..10}
do
   while true; do curl -s http://localhost:30001 > /dev/null; done &
done

echo "Trafik sedang dikirim... Pantau pods dengan: kubectl get hpa -w"
wait
