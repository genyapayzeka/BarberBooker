# WhatsApp Integration Guide

This document explains how to set up and use the WhatsApp integration for the Barber Appointment System.

## Overview

The system integrates with WhatsApp through the WhatsApp Business API, allowing customers to:

- Register as a new customer
- Book, modify, and cancel appointments
- Check appointment status
- Get information about services, barbers, and business hours
- Ask general questions that are processed through ChatGPT

## Prerequisites

Before setting up the WhatsApp integration, you need:

1. A WhatsApp Business Account
2. Access to the WhatsApp Business API (through Meta/Facebook)
3. A Facebook Developer Account
4. A publicly accessible server to host your webhook (the system needs to be accessible from the internet)

## Setup Steps

### 1. Create a Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "My Apps" and then "Create App"
3. Select "Business" as the app type
4. Follow the steps to create your app
5. Note your App ID for future reference

### 2. Set Up WhatsApp in Your Meta App

1. From your app dashboard, click "Add Products" and select "WhatsApp"
2. Follow the setup process to connect your WhatsApp business phone number
3. Once set up, go to the "API Setup" section and note down:
   - Phone Number ID
   - WhatsApp Business Account ID
   - Access Token (Generate a Permanent Token)

### 3. Configure Your Webhook

1. In your Meta App dashboard, go to "Webhooks" under the WhatsApp product
2. Click "Configure Webhooks"
3. Enter your Callback URL (your server URL + `/webhook`), e.g., `https://your-domain.com/webhook`
4. Enter your Verify Token (this should match the `WHATSAPP_VERIFY_TOKEN` in your `.env` file)
5. Select the following subscription fields:
   - messages
   - message_deliveries
   - message_reads
   - message_reactions
6. Click "Verify and Save"

### 4. Configure Environment Variables

Update your `.env` file with the WhatsApp API credentials:

