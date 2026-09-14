FROM alpine:latest

# Install dnsmasq
RUN apk add --no-cache dnsmasq

# Copy dnsmasq configuration
COPY config/dnsmasq.conf /etc/dnsmasq.conf

# Expose DNS port (53/udp)
EXPOSE 53/udp

# Start dnsmasq
CMD ["dnsmasq", "--no-daemon", "--log-facility=-"]
